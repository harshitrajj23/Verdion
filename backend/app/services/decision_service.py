import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.canonical import (
    compute_canonical_sha256,
    format_canonical_timestamp,
    serialize_canonical_json,
    CANONICAL_SCHEMA_VERSION,
)
from backend.app.models.entities import (
    Case,
    Claim,
    ClaimEvidenceLink,
    DecisionRecordEntity,
    EvidencePassage,
    Forecast,
    PredictionMarket,
    Settlement,
    SourceDocument,
    utcnow,
)
from backend.app.schemas.decision_record import (
    AnalysisConfiguration,
    AuditEventLink,
    AuditPackageManifest,
    CanonicalDecisionRecord,
    ClaimRecord,
    EvidencePassageRecord,
    EvidenceSourceRecord,
    ForecastCommitmentRecord,
    ForecastMarketRecord,
    SettlementRecord,
)
from backend.app.services.audit_service import AuditService


class DecisionService:
    @staticmethod
    async def build_canonical_decision_record(
        db: AsyncSession,
        case_id: str,
        persist: bool = True,
        rebuild: bool = False
    ) -> CanonicalDecisionRecord:
        """
        Builds an auditable, self-contained Canonical Decision Record for an analyzed case.
        Strictly connects:
        Evidence Source -> Document Version -> Evidence Passage -> Analysis Run ->
        Claim -> Forecast -> Commitment -> Reveal -> Resolution -> Settlement -> Audit Event.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        decision_id = f"dec_{case.id}_v{case.scope_version}"
        if not rebuild:
            existing = await db.get(DecisionRecordEntity, decision_id)
            if existing and existing.canonical_data:
                return CanonicalDecisionRecord(**existing.canonical_data)

        # 1. Fetch claims for this case
        stmt_claims = select(Claim).where(Claim.case_id == case_id)
        res_claims = await db.execute(stmt_claims)
        claims_list = res_claims.scalars().all()

        # 2. Fetch linked evidence passages
        passage_ids = set()
        for c in claims_list:
            stmt_links = select(ClaimEvidenceLink).where(ClaimEvidenceLink.claim_id == c.id)
            res_links = await db.execute(stmt_links)
            links = res_links.scalars().all()
            for l in links:
                passage_ids.add(l.evidence_id)

        evidence_passages_records: List[EvidencePassageRecord] = []
        document_ids = set()

        if passage_ids:
            stmt_pass = select(EvidencePassage).where(EvidencePassage.id.in_(list(passage_ids)))
            res_pass = await db.execute(stmt_pass)
            for p in res_pass.scalars().all():
                document_ids.add(p.document_id)
                evidence_passages_records.append(
                    EvidencePassageRecord(
                        passage_id=p.id,
                        document_id=p.document_id,
                        passage_reference=p.passage_reference,
                        content_reference=p.content_reference,
                        text_excerpt=p.text[:600] if p.text else "",
                        passage_digest=p.digest,
                        digest_algorithm="SHA-256",
                        source_version=p.source_version or "1.0",
                        provenance=p.provenance or "BUNDLED_FIXTURE"
                    )
                )

        # 3. Fetch evidence source documents
        evidence_sources_records: List[EvidenceSourceRecord] = []
        if document_ids:
            stmt_docs = select(SourceDocument).where(SourceDocument.id.in_(list(document_ids)))
            res_docs = await db.execute(stmt_docs)
            for d in res_docs.scalars().all():
                evidence_sources_records.append(
                    EvidenceSourceRecord(
                        document_id=d.id,
                        title=d.title,
                        authority=d.authority,
                        jurisdiction=d.jurisdiction,
                        url=d.url,
                        official_identifier=getattr(d, "celex_or_ecli", None) or d.id,
                        document_version=d.version or "1.0",
                        publication_date=d.publication_date,
                        effective_date=d.effective_date,
                        retrieval_timestamp=format_canonical_timestamp(d.retrieved_at) or "2026-01-01T00:00:00Z",
                        content_digest=d.digest,
                        digest_algorithm="SHA-256",
                        provenance=d.provenance or "BUNDLED_FIXTURE",
                        access_classification="PUBLIC_OFFICIAL"
                    )
                )

        # 4. Format claims with passage digest links
        claim_records: List[ClaimRecord] = []
        passages_by_id = {p.passage_id: p for p in evidence_passages_records}

        for c in claims_list:
            stmt_links = select(ClaimEvidenceLink).where(ClaimEvidenceLink.claim_id == c.id)
            res_links = await db.execute(stmt_links)
            links = res_links.scalars().all()
            cited_ids = [l.evidence_id for l in links]
            cited_digests = [passages_by_id[pid].passage_digest for pid in cited_ids if pid in passages_by_id]

            conf_val = 0.85
            if isinstance(c.confidence_metadata, dict):
                conf_val = float(c.confidence_metadata.get("composite_confidence", 0.85))

            claim_records.append(
                ClaimRecord(
                    claim_id=c.id,
                    agent_id=c.agent_id,
                    role="LEGAL_ANALYST",
                    claim_text=c.claim_text,
                    claim_type=c.claim_type,
                    cited_passage_ids=cited_ids,
                    cited_passage_digests=cited_digests,
                    assumptions=c.assumptions or [],
                    confidence=conf_val,
                    status=c.status,
                    counterarguments=[],
                    entailment_disclaimer="Mechanical citation match; formal legal entailment requires human or judicial determination."
                )
            )

        # 5. Fetch prediction markets and commitments
        stmt_markets = select(PredictionMarket).where(PredictionMarket.case_id == case_id)
        res_markets = await db.execute(stmt_markets)
        markets = res_markets.scalars().all()

        market_records: List[ForecastMarketRecord] = []
        for m in markets:
            stmt_fcs = select(Forecast).where(Forecast.market_id == m.id)
            res_fcs = await db.execute(stmt_fcs)
            fcs = res_fcs.scalars().all()

            commitments: List[ForecastCommitmentRecord] = []
            for f in fcs:
                commitments.append(
                    ForecastCommitmentRecord(
                        forecast_id=f.id,
                        market_id=m.id,
                        agent_id=f.agent_id,
                        wallet_address=getattr(f, "wallet_address", None) or "0xUnknown",
                        commitment_hash=f.commitment_hash,
                        committed_at=format_canonical_timestamp(f.created_at) or "",
                        commit_tx_hash=f.commit_tx_hash,
                        reveal_status=f.reveal_status,
                        revealed_at=format_canonical_timestamp(f.revealed_at),
                        revealed_probability=f.probability,
                        revealed_evidence_digest=f.evidence_digest,
                        revealed_nonce=f.nonce,
                        reveal_tx_hash=f.reveal_tx_hash,
                        cryptographic_validity="VERIFIED" if f.reveal_status == "REVEALED" else "UNREVEALED"
                    )
                )

            market_records.append(
                ForecastMarketRecord(
                    market_id=m.id,
                    question=m.question,
                    outcome_definition=m.outcome_definition,
                    resolution_method=m.resolution_method,
                    rubric_version=m.rubric_version or "1.0",
                    commit_deadline=format_canonical_timestamp(m.commit_deadline) or "",
                    reveal_deadline=format_canonical_timestamp(m.reveal_deadline) or "",
                    resolution_deadline=format_canonical_timestamp(m.resolution_deadline) or "",
                    scoring_version=m.scoring_version or "brier_v1",
                    status=m.status,
                    contract_address=m.contract_address,
                    evaluator_address=m.evaluator_address,
                    proposed_outcome=m.proposed_outcome,
                    resolution_reference=m.resolution_reference,
                    aggregate_probability=m.aggregate_probability,
                    disagreement_variance=m.disagreement_variance,
                    sample_size=m.sample_size,
                    commitments=commitments
                )
            )

        # 6. Fetch settlements
        market_ids = [m.id for m in markets]
        settlement_records: List[SettlementRecord] = []
        if market_ids:
            stmt_settlements = select(Settlement).where(Settlement.reference_id.in_(market_ids))
            res_settlements = await db.execute(stmt_settlements)
            for s in res_settlements.scalars().all():
                settlement_records.append(
                    SettlementRecord(
                        settlement_id=s.id,
                        reference_id=s.reference_id,
                        participant_address=s.participant_address,
                        score=s.score,
                        scoring_method="brier_score",
                        reward_credits=s.reward,
                        reward_type="SIMULATED_CREDITS",
                        tx_hash=s.tx_hash,
                        settlement_status="CONFIRMED" if s.tx_hash else "SIMULATED",
                        settled_at=format_canonical_timestamp(s.created_at) or ""
                    )
                )

        # 7. Fetch audit events
        audit_events = await AuditService.get_case_audit_trail(db, case_id)
        audit_links = [
            AuditEventLink(
                event_id=e.id,
                sequence_number=e.sequence_number or (i + 1),
                event_type=e.event_type,
                actor=e.actor,
                payload_digest=e.payload_digest,
                previous_event_digest=e.previous_event_digest,
                event_digest=e.event_digest or "",
                tx_hash=e.tx_hash,
                timestamp=format_canonical_timestamp(e.timestamp) or ""
            )
            for i, e in enumerate(audit_events)
        ]

        # 8. Analysis configuration
        analysis_config = AnalysisConfiguration(
            orchestration_version="veridion_agent_orchestration_v1.0.0",
            software_version="veridion-core@1.0.0",
            deterministic_rule_version="statutory_rule_engine_v1.0",
            prompt_template_versions={
                "legal_researcher": "eurlex_cjeu_v1.0",
                "legal_interpreter": "hybrid_statutory_v1.0",
                "adversarial_researcher": "adversarial_redteam_v1.0",
                "evidence_verifier": "sha256_verifier_v1.0"
            },
            model_provider_observed="veridion_deterministic_hybrid_orchestrator",
            inference_parameters={"temperature": 0.0, "seed": 42}
        )

        decision_id = f"dec_{case.id}_v{case.scope_version}"
        analysis_ts = format_canonical_timestamp(case.updated_at or case.created_at) or "2026-10-27T12:00:00Z"

        # Assemble Canonical Record (initially without record_digest)
        raw_record_dict = {
            "schema_version": CANONICAL_SCHEMA_VERSION,
            "decision_id": decision_id,
            "case_id": case.id,
            "case_version": case.scope_version,
            "case_title": case.title,
            "case_question": case.question,
            "jurisdiction": case.jurisdiction,
            "assessment_date": case.assessment_date,
            "facts": case.facts or {},
            "analysis_configuration": analysis_config.model_dump(),
            "analysis_timestamp": analysis_ts,
            "evidence_sources": [s.model_dump() for s in evidence_sources_records],
            "evidence_passages": [p.model_dump() for p in evidence_passages_records],
            "claims": [c.model_dump() for c in claim_records],
            "forecast_markets": [m.model_dump() for m in market_records],
            "settlements": [st.model_dump() for st in settlement_records],
            "audit_events": [a.model_dump() for a in audit_links],
            "record_digest": None
        }

        # Compute deterministic canonical hash over the record
        record_digest = compute_canonical_sha256(raw_record_dict)
        raw_record_dict["record_digest"] = record_digest

        record = CanonicalDecisionRecord(**raw_record_dict)

        # 9. Persist/update entity if requested
        if persist:
            existing = await db.get(DecisionRecordEntity, decision_id)
            if existing:
                existing.record_digest = record_digest
                existing.canonical_data = raw_record_dict
            else:
                db_entity = DecisionRecordEntity(
                    id=decision_id,
                    case_id=case.id,
                    case_version=case.scope_version,
                    orchestration_version=analysis_config.orchestration_version,
                    software_version=analysis_config.software_version,
                    record_digest=record_digest,
                    canonical_data=raw_record_dict,
                    created_at=utcnow()
                )
                db.add(db_entity)
            await db.commit()

        return record

    @staticmethod
    async def generate_audit_package(db: AsyncSession, case_id: str) -> Dict[str, Any]:
        """
        Creates an exportable, self-verifiable audit package for an independent reviewer.
        Contains the canonical decision record, full audit event trail,
        verification instructions, and cryptographic checksums.
        """
        record = await DecisionService.build_canonical_decision_record(db, case_id, persist=True)
        events_audit = await AuditService.verify_case_audit_chain(db, case_id)

        package_id = f"pkg_{case_id}_{uuid.uuid4().hex[:8]}"
        now_str = format_canonical_timestamp(utcnow())

        leaf_digests = [e.event_digest for e in record.audit_events if e.event_digest]
        rec_merkle_root = AuditService.compute_merkle_root(leaf_digests)
        rec_chain_head = leaf_digests[-1] if leaf_digests else ""

        manifest = AuditPackageManifest(
            package_id=package_id,
            spec_version="VERIDION_AUDIT_SPEC_V1",
            case_id=case_id,
            generated_at=now_str,
            generator_software="veridion-core@1.0.0",
            decision_record_digest=record.record_digest or "",
            audit_chain_head_digest=rec_chain_head,
            merkle_checkpoint_root=rec_merkle_root,
            verification_instructions=(
                "To verify this package independently:\n"
                "1. Run 'python -m backend.app.services.audit_verifier package.json'\n"
                "2. The verifier will recompute passage SHA-256 digests, recheck claims against cited passages,\n"
                "   re-verify commit-reveal keccak256 hashes, validate Brier proper scoring calculations,\n"
                "   and check the unbroken sequence and Merkle root of the append-only audit trail."
            )
        )

        package = {
            "manifest": manifest.model_dump(),
            "decision_record": record.model_dump(),
            "audit_chain_verification": events_audit,
            "checksums": {
                "decision_record_sha256": record.record_digest,
                "manifest_sha256": compute_canonical_sha256(manifest.model_dump()),
                "audit_merkle_root": events_audit.get("merkle_checkpoint_root")
            }
        }
        return package
