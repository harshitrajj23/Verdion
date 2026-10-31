import time
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.entities import SourceDocument, EvidencePassage, Case, EvidenceBounty, utcnow
from backend.app.services.audit_service import AuditService
from backend.app.services.ingestion.base_adapter import (
    BaseSourceAdapter,
    SourceDocumentMetadata,
    ExternalSourceRetrievalError,
)
from backend.app.services.ingestion.eur_lex_adapter import EURLexAdapter
from backend.app.services.ingestion.cjeu_adapter import CJEUAdapter
from backend.app.services.ingestion.edpb_adapter import EDPBAdapter


class IngestionJobRecord:
    def __init__(self, job_id: str, adapter_name: str, identifier: Optional[str] = None):
        self.job_id = job_id
        self.adapter_name = adapter_name
        self.identifier = identifier
        self.status = "RUNNING"
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
        self.documents_discovered: int = 0
        self.documents_fetched: int = 0
        self.new_versions: int = 0
        self.duplicates_skipped: int = 0
        self.passages_created: int = 0
        self.ingested_documents: List[Dict[str, Any]] = []
        self.cases_marked_for_reanalysis: List[str] = []
        self.proposed_bounties: List[Dict[str, Any]] = []
        self.error: Optional[str] = None

    def complete(self, status: str = "COMPLETED", error: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "adapter_name": self.adapter_name,
            "identifier": self.identifier,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "documents_discovered": self.documents_discovered,
            "documents_fetched": self.documents_fetched,
            "new_versions": self.new_versions,
            "duplicates_skipped": self.duplicates_skipped,
            "passages_created": self.passages_created,
            "ingested_documents": self.ingested_documents,
            "cases_marked_for_reanalysis": self.cases_marked_for_reanalysis,
            "proposed_bounties": self.proposed_bounties,
            "error": self.error
        }


# Global in-memory telemetry registry for ingestion jobs & re-analysis proposals
JOB_HISTORY: List[IngestionJobRecord] = []
REANALYSIS_PROPOSALS: List[Dict[str, Any]] = []


class IngestionService:
    ADAPTERS: Dict[str, BaseSourceAdapter] = {
        "eur_lex": EURLexAdapter(),
        "cjeu": CJEUAdapter(),
        "edpb": EDPBAdapter()
    }

    @classmethod
    def get_adapter(cls, name: str) -> Optional[BaseSourceAdapter]:
        return cls.ADAPTERS.get(name.lower())

    @classmethod
    async def trigger_ingestion(
        cls,
        db: AsyncSession,
        adapter_name: str = "eur_lex",
        identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        adapter = cls.get_adapter(adapter_name)
        if not adapter:
            raise ValueError(f"Unknown legal source adapter '{adapter_name}'. Available: {list(cls.ADAPTERS.keys())}")

        job_id = f"job_ingest_{uuid.uuid4().hex[:10]}"
        job = IngestionJobRecord(job_id=job_id, adapter_name=adapter_name, identifier=identifier)
        JOB_HISTORY.insert(0, job)

        try:
            # Fetch either specific document by identifier or feed
            if identifier and identifier.strip():
                single_doc = await adapter.fetch_document(identifier.strip())
                feed_docs = [single_doc]
            else:
                feed_docs = await adapter.fetch_feed(limit=2)

            job.documents_discovered = len(feed_docs)

            for doc in feed_docs:
                existing = await db.get(SourceDocument, doc.source_id)

                if existing:
                    if existing.digest == doc.digest and existing.version == doc.version:
                        # Exact duplicate by cryptographic digest - skip idempotently
                        job.duplicates_skipped += 1
                        job.ingested_documents.append({
                            "source_id": doc.source_id,
                            "title": doc.title,
                            "digest": doc.digest,
                            "action": "SKIPPED_IDEMPOTENT_DUPLICATE",
                            "provenance": existing.provenance or doc.provenance
                        })
                        continue
                    else:
                        # Changed version detected - update and preserve version history
                        old_ver = existing.version
                        try:
                            # Bump minor version e.g. 1.0 -> 1.1
                            v_parts = old_ver.split(".")
                            new_ver = f"{v_parts[0]}.{int(v_parts[1]) + 1}"
                        except Exception:
                            new_ver = f"{old_ver}.1"

                        existing.version = new_ver
                        existing.digest = doc.digest
                        existing.raw_content = doc.raw_content
                        existing.retrieved_at = utcnow()
                        existing.provenance = doc.provenance
                        job.new_versions += 1
                        job.documents_fetched += 1
                        job.ingested_documents.append({
                            "source_id": doc.source_id,
                            "title": doc.title,
                            "version": new_ver,
                            "digest": doc.digest,
                            "action": "VERSION_UPDATED",
                            "provenance": doc.provenance
                        })
                else:
                    # New primary legal document
                    new_doc = SourceDocument(
                        id=doc.source_id,
                        title=doc.title,
                        authority=f"{doc.jurisdiction} Official Publication ({doc.document_type})",
                        jurisdiction=doc.jurisdiction,
                        url=doc.url,
                        publication_date=doc.publication_date,
                        effective_date=doc.effective_date,
                        digest=doc.digest,
                        version=doc.version,
                        provenance=doc.provenance,
                        raw_content=doc.raw_content,
                        retrieved_at=utcnow()
                    )
                    db.add(new_doc)
                    job.documents_fetched += 1
                    job.ingested_documents.append({
                        "source_id": doc.source_id,
                        "title": doc.title,
                        "version": doc.version,
                        "digest": doc.digest,
                        "action": "INSERTED_NEW",
                        "provenance": doc.provenance
                    })

                # Segment into discrete passage references and store
                passages = adapter.segment_passages(doc)
                for p in passages:
                    existing_p = await db.get(EvidencePassage, p["id"])
                    if not existing_p:
                        new_p = EvidencePassage(
                            id=p["id"],
                            document_id=p["document_id"],
                            passage_reference=p["passage_reference"],
                            content_reference=p["content_reference"],
                            text=p["text"],
                            digest=p["digest"],
                            source_version=p["source_version"],
                            provenance=doc.provenance
                        )
                        db.add(new_p)
                        job.passages_created += 1

                await db.flush()

                # Impact Analysis: Find cases whose factual scope intersects with the new legislation
                affected_cases = await cls._identify_affected_cases(db, doc)
                for case_id in affected_cases:
                    if case_id not in job.cases_marked_for_reanalysis:
                        job.cases_marked_for_reanalysis.append(case_id)
                        proposal = {
                            "proposal_id": f"prop_{uuid.uuid4().hex[:10]}",
                            "case_id": case_id,
                            "trigger_source_id": doc.source_id,
                            "trigger_title": doc.title,
                            "reason": f"New statutory provisions in {doc.celex_or_ecli or doc.source_id} affect case facts",
                            "status": "QUEUED_FOR_REANALYSIS",
                            "created_at": utcnow().isoformat()
                        }
                        REANALYSIS_PROPOSALS.insert(0, proposal)

                # Proposed Evidence Bounty if significant regulatory shift
                if doc.document_type in ["REGULATION", "CORRIGENDUM", "CJEU_JUDGMENT"]:
                    bounty_proposal = {
                        "proposed_bounty_title": f"Bounty: Verify compliance against {doc.title[:60]}...",
                        "jurisdiction": doc.jurisdiction,
                        "statutory_ref": doc.celex_or_ecli or doc.source_id,
                        "recommended_reward_credits": 500.0,
                        "status": "PROPOSED_READY_FOR_CREATION"
                    }
                    job.proposed_bounties.append(bounty_proposal)

            await db.commit()

            # Record auditable event
            audit_case_id = job.cases_marked_for_reanalysis[0] if job.cases_marked_for_reanalysis else None
            if not audit_case_id:
                res = await db.execute(select(Case.id).limit(1))
                audit_case_id = res.scalar_one_or_none()

            if audit_case_id:
                await AuditService.log_event(
                    db=db,
                    case_id=audit_case_id,
                    event_type="REGULATORY_INGESTION_COMPLETED",
                    actor=f"Adapter:{adapter_name}",
                    payload=job.to_dict()
                )

            final_status = "COMPLETED" if job.documents_fetched > 0 or job.duplicates_skipped > 0 else "FAILED"
            job.complete(status=final_status)
            return job.to_dict()

        except Exception as e:
            await db.rollback()
            job.complete(status="FAILED", error=str(e))
            # Log failed audit event if possible
            try:
                res = await db.execute(select(Case.id).limit(1))
                c_id = res.scalar_one_or_none()
                if c_id:
                    await AuditService.log_event(
                        db=db,
                        case_id=c_id,
                        event_type="REGULATORY_INGESTION_FAILED",
                        actor=f"Adapter:{adapter_name}",
                        payload={"error": str(e), "identifier": identifier}
                    )
                    await db.commit()
            except Exception:
                pass

            return job.to_dict()

    @classmethod
    async def _identify_affected_cases(cls, db: AsyncSession, doc: SourceDocumentMetadata) -> List[str]:
        """Identifies existing cases whose factual scope warrants re-analysis under new law."""
        stmt = select(Case).order_by(Case.created_at.desc()).limit(15)
        res = await db.execute(stmt)
        cases = res.scalars().all()
        affected = []

        keywords = ["ai", "training", "biometric", "research", "scientific", "automated", "retention", "access", "model"]
        doc_lower = doc.raw_content.lower() + " " + doc.title.lower()

        for c in cases:
            case_text = (c.title + " " + (c.question or "")).lower()
            facts_text = str(c.facts or "").lower()
            combined = case_text + " " + facts_text

            matches = [kw for kw in keywords if kw in combined and kw in doc_lower]
            if matches:
                affected.append(c.id)

        return affected

    @classmethod
    def list_jobs(cls) -> List[Dict[str, Any]]:
        return [j.to_dict() for j in JOB_HISTORY]

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        for j in JOB_HISTORY:
            if j.job_id == job_id:
                return j.to_dict()
        return None

    @classmethod
    def list_proposals(cls) -> List[Dict[str, Any]]:
        return list(REANALYSIS_PROPOSALS)
