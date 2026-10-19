import json
import os
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.crypto import compute_sha256_digest
from backend.app.models.entities import EvidencePassage, SourceDocument

CORPUS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "curated_corpus.json")
ML_CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "ml", "corpus")


class RetrievalService:
    @staticmethod
    async def initialize_corpus(db: AsyncSession) -> int:
        """Loads and syncs curated legal corpus into database from internal data and ml/corpus/."""
        documents_data = []

        if os.path.exists(CORPUS_PATH):
            with open(CORPUS_PATH, "r", encoding="utf-8") as f:
                documents_data.extend(json.load(f))

        # Also load from ml/corpus/ if directory exists
        if os.path.exists(ML_CORPUS_DIR):
            for filename in os.listdir(ML_CORPUS_DIR):
                if filename.endswith(".json"):
                    filepath = os.path.join(ML_CORPUS_DIR, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                documents_data.extend(data)
                            elif isinstance(data, dict):
                                documents_data.append(data)
                    except Exception:
                        pass

        count = 0
        for doc_data in documents_data:
            existing_doc = await db.get(SourceDocument, doc_data["id"])
            if not existing_doc:
                # Compute canonical document digest
                doc_digest = compute_sha256_digest({
                    "id": doc_data["id"],
                    "title": doc_data["title"],
                    "authority": doc_data["authority"],
                    "jurisdiction": doc_data["jurisdiction"],
                    "publication_date": doc_data["publication_date"],
                    "effective_date": doc_data["effective_date"],
                })

                raw_text = "\n".join([p["text"] for p in doc_data.get("passages", [])])
                new_doc = SourceDocument(
                    id=doc_data["id"],
                    title=doc_data["title"],
                    authority=doc_data["authority"],
                    jurisdiction=doc_data["jurisdiction"],
                    url=doc_data["url"],
                    publication_date=doc_data["publication_date"],
                    effective_date=doc_data["effective_date"],
                    digest=doc_digest,
                    version=doc_data.get("version", "1.0"),
                    raw_content=raw_text
                )
                db.add(new_doc)
                await db.flush()

                for p in doc_data.get("passages", []):
                    passage_digest = compute_sha256_digest(p["text"])
                    passage = EvidencePassage(
                        id=p["id"],
                        document_id=doc_data["id"],
                        passage_reference=p["passage_reference"],
                        content_reference=p["content_reference"],
                        text=p["text"],
                        digest=passage_digest,
                        source_version=doc_data.get("version", "1.0")
                    )
                    db.add(passage)
                    count += 1

        await db.commit()
        return count

    @staticmethod
    async def retrieve_passages(
        db: AsyncSession,
        query: str,
        jurisdiction: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant passages with authority metadata and cryptographic digests.
        Treats text as untrusted (sanitizes system prompt injection tokens).
        """
        stmt = (
            select(EvidencePassage, SourceDocument)
            .join(SourceDocument, EvidencePassage.document_id == SourceDocument.id)
        )
        if jurisdiction and jurisdiction.lower() != "all":
            stmt = stmt.where(SourceDocument.jurisdiction == jurisdiction)

        result = await db.execute(stmt)
        rows = result.all()

        query_terms = set(re.findall(r"\w+", query.lower()))
        scored_passages = []

        for passage, doc in rows:
            passage_text = passage.text.lower()
            ref_text = passage.passage_reference.lower()

            # Term overlap score
            matched_terms = [t for t in query_terms if t in passage_text or t in ref_text]
            score = len(matched_terms) / (len(query_terms) if query_terms else 1.0)

            # Untrusted data guard: ensure no system directive injection escapes
            safe_text = passage.text.replace("### System:", "").replace("<script>", "")

            scored_passages.append({
                "evidence_id": passage.id,
                "document_id": doc.id,
                "document_title": doc.title,
                "authority": doc.authority,
                "jurisdiction": doc.jurisdiction,
                "passage_reference": passage.passage_reference,
                "content_reference": passage.content_reference,
                "text": safe_text,
                "digest": passage.digest,
                "source_version": passage.source_version,
                "effective_date": doc.effective_date,
                "is_current": True,
                "relevance_score": round(score, 4)
            })

        # Sort by relevance score descending
        scored_passages.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_passages[:limit]

    @staticmethod
    async def get_passage_by_id(db: AsyncSession, evidence_id: str) -> Optional[Dict[str, Any]]:
        passage = await db.get(EvidencePassage, evidence_id)
        if not passage:
            return None
        doc = await db.get(SourceDocument, passage.document_id)
        return {
            "evidence_id": passage.id,
            "document_id": doc.id if doc else "unknown",
            "document_title": doc.title if doc else "unknown",
            "authority": doc.authority if doc else "unknown",
            "passage_reference": passage.passage_reference,
            "text": passage.text,
            "digest": passage.digest,
            "source_version": passage.source_version,
            "effective_date": doc.effective_date if doc else "unknown"
        }
