import json
import os
import sys
from typing import List, Dict, Any, Optional

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.src.canonicalDigest import compute_evidence_digest
from ml.retrieval.isolation import PromptInjectionIsolation

class LegalRetriever:
    """
    Retrieval engine with passage provenance, effective-date tracking,
    and prompt-injection isolation (FR-006, FR-007, FR-008, FR-010, FR-024).
    """

    def __init__(self, corpus_path: Optional[str] = None, passages_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.corpus_path = corpus_path or os.path.join(base_dir, "corpus", "corpus_metadata.json")
        self.passages_path = passages_path or os.path.join(base_dir, "corpus", "passages.json")
        
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            self.corpus_metadata = json.load(f)
            
        with open(self.passages_path, "r", encoding="utf-8") as f:
            self.passages = json.load(f)

    def search_passages(self, query: str, assessment_date: str = "2026-03-15", top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves matching passages, filters by effective date (FR-010),
        computes evidence digest (FR-026), and formats isolated representation (FR-012).
        """
        query_tokens = set(query.lower().split())
        scored = []

        for p in self.passages:
            # Check effective date: passage must be in effect on assessment date
            if p.get("effective_date", "9999") > assessment_date:
                continue

            content_text = (p.get("content", "") + " " + p.get("passage_reference", "")).lower()
            keywords = p.get("keywords", [])
            
            score = 0
            for token in query_tokens:
                if len(token) > 2 and token in content_text:
                    score += 1
            for kw in keywords:
                if any(k_part in query.lower() for k_part in kw.split()):
                    score += 2

            if score > 0:
                scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []

        for score, passage in scored[:top_k]:
            evidence_payload = {
                "document_id": passage["document_id"],
                "passage_reference": passage["passage_reference"],
                "content": passage["content"],
                "source_metadata": {
                    "title": passage["passage_reference"],
                    "authority": passage["authority"],
                    "jurisdiction": self.corpus_metadata["jurisdiction"],
                    "effective_date": passage["effective_date"]
                }
            }
            digest = compute_evidence_digest(evidence_payload)
            isolated_xml = PromptInjectionIsolation.format_isolated_passage(passage)

            results.append({
                "passage_id": passage["passage_id"],
                "document_id": passage["document_id"],
                "passage_reference": passage["passage_reference"],
                "content": passage["content"],
                "authority": passage["authority"],
                "effective_date": passage["effective_date"],
                "relevance_score": score,
                "digest": digest,
                "isolated_xml": isolated_xml
            })

        return results
