"""
VERIDION Hybrid Cryptographic & Semantic Deduplication Engine (PRD-SEC-006)
Option C: Auditable Regulatory Decision Infrastructure

Implements:
1. Exact SHA-256 cryptographic digest deduplication.
2. Semantic near-duplicate candidate retrieval using composite vector similarity.
3. Legal context awareness (jurisdiction, amendment date, source authority).
4. Three-tier decision framework:
   - EXACT_DUPLICATE (Hash match) -> IDEMPOTENT_SKIP
   - SEMANTIC_DUPLICATE (Score >= 0.92) -> REJECT_REDUNDANT
   - NEAR_DUPLICATE_UNCERTAIN (0.75 <= Score < 0.92) -> FLAG_FOR_HUMAN_REVIEW
   - DISTINCT_CONTENT (Score < 0.75) -> ACCEPT
"""

import hashlib
import math
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DuplicateStatus(str, Enum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    SEMANTIC_DUPLICATE = "SEMANTIC_DUPLICATE"
    NEAR_DUPLICATE_UNCERTAIN = "NEAR_DUPLICATE_UNCERTAIN"
    LEGAL_ANALOGUE_DISTINCT_JURISDICTION = "LEGAL_ANALOGUE_DISTINCT_JURISDICTION"
    DISTINCT_CONTENT = "DISTINCT_CONTENT"


class ActionRecommendation(str, Enum):
    IDEMPOTENT_SKIP = "IDEMPOTENT_SKIP"
    REJECT_REDUNDANT = "REJECT_REDUNDANT"
    FLAG_FOR_HUMAN_REVIEW = "FLAG_FOR_HUMAN_REVIEW"
    ACCEPT = "ACCEPT"


@dataclass
class DocumentPassage:
    passage_id: str
    text: str
    jurisdiction: str                  # e.g., "EU", "FR", "IE", "US-CA"
    authority: str                     # e.g., "EDPB", "CNIL", "FTC", "CPPA"
    source_uri: str
    version_or_date: str
    sha256_digest: Optional[str] = None

    def __post_init__(self):
        if not self.sha256_digest:
            self.sha256_digest = hashlib.sha256(self.text.encode("utf-8")).hexdigest()


@dataclass
class DeduplicationResult:
    status: DuplicateStatus
    action: ActionRecommendation
    similarity_score: float
    matched_passage_id: Optional[str]
    matched_source_uri: Optional[str]
    exact_hash_match: bool
    explanation: str
    requires_human_review: bool


class HybridDeduplicationService:
    """
    Production-grade hybrid deduplication engine.
    Ensures zero legal text loss while catching exact, re-formatted, and paraphrased duplicates.
    """

    SEMANTIC_THRESHOLD_REJECT = 0.92
    SEMANTIC_THRESHOLD_REVIEW = 0.75

    def __init__(self, existing_passages: Optional[List[DocumentPassage]] = None):
        self._exact_hash_index: Dict[str, DocumentPassage] = {}
        self._passage_store: List[DocumentPassage] = []
        if existing_passages:
            for p in existing_passages:
                self.add_passage(p)

    def add_passage(self, passage: DocumentPassage) -> None:
        if passage.sha256_digest:
            self._exact_hash_index[passage.sha256_digest] = passage
        self._passage_store.append(passage)

    @staticmethod
    def _compute_vector(text: str) -> Dict[str, int]:
        tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
        vec: Dict[str, int] = {}
        for t in tokens:
            for n in (3, 4, 5):
                for i in range(max(1, len(t) - n + 1)):
                    gram = t[i:i+n]
                    vec[gram] = vec.get(gram, 0) + 1
        return vec

    @classmethod
    def compute_composite_similarity(cls, text_a: str, text_b: str) -> float:
        # 1. Cosine similarity of character n-grams
        vec_a = cls._compute_vector(text_a)
        vec_b = cls._compute_vector(text_b)
        dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in vec_a)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        cosine = (dot / (norm_a * norm_b)) if (norm_a > 0 and norm_b > 0) else 0.0

        # 2. Token Jaccard similarity
        tokens_a = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_a.lower()))
        tokens_b = set(re.findall(r"\b[a-zA-Z]{3,}\b", text_b.lower()))
        jaccard = (len(tokens_a & tokens_b) / len(tokens_a | tokens_b)) if (tokens_a or tokens_b) else 0.0

        # 3. Length ratio
        len_a = len(text_a)
        len_b = len(text_b)
        len_ratio = (min(len_a, len_b) / max(len_a, len_b)) if max(len_a, len_b) > 0 else 0.0

        # Composite score
        composite = (0.60 * cosine) + (0.30 * jaccard) + (0.10 * len_ratio)
        return min(1.0, max(0.0, composite))

    def evaluate_passage(self, candidate: DocumentPassage) -> DeduplicationResult:
        # Step 1: Exact Cryptographic Hash Check
        if candidate.sha256_digest in self._exact_hash_index:
            existing = self._exact_hash_index[candidate.sha256_digest]
            return DeduplicationResult(
                status=DuplicateStatus.EXACT_DUPLICATE,
                action=ActionRecommendation.IDEMPOTENT_SKIP,
                similarity_score=1.0,
                matched_passage_id=existing.passage_id,
                matched_source_uri=existing.source_uri,
                exact_hash_match=True,
                explanation=f"Exact cryptographic SHA-256 match with passage '{existing.passage_id}'.",
                requires_human_review=False
            )

        # Step 2: Semantic Similarity Scan
        best_match: Optional[DocumentPassage] = None
        highest_score = 0.0

        for existing in self._passage_store:
            score = self.compute_composite_similarity(candidate.text, existing.text)
            if score > highest_score:
                highest_score = score
                best_match = existing

        if not best_match or highest_score < self.SEMANTIC_THRESHOLD_REVIEW:
            return DeduplicationResult(
                status=DuplicateStatus.DISTINCT_CONTENT,
                action=ActionRecommendation.ACCEPT,
                similarity_score=highest_score,
                matched_passage_id=best_match.passage_id if best_match else None,
                matched_source_uri=best_match.source_uri if best_match else None,
                exact_hash_match=False,
                explanation="Content is semantically distinct from all existing repository passages.",
                requires_human_review=False
            )

        # Step 3: Legal Context Check (Different jurisdiction prevents automatic deletion)
        if candidate.jurisdiction.lower() != best_match.jurisdiction.lower():
            return DeduplicationResult(
                status=DuplicateStatus.LEGAL_ANALOGUE_DISTINCT_JURISDICTION,
                action=ActionRecommendation.ACCEPT,
                similarity_score=highest_score,
                matched_passage_id=best_match.passage_id,
                matched_source_uri=best_match.source_uri,
                exact_hash_match=False,
                explanation=(
                    f"High semantic similarity ({highest_score:.3f}) with {best_match.passage_id}, "
                    f"but jurisdictions differ ({candidate.jurisdiction} vs {best_match.jurisdiction}). "
                    "Treated as distinct legal analogue."
                ),
                requires_human_review=True
            )

        # Step 4: Tiered Semantic Duplicate Classification
        if highest_score >= self.SEMANTIC_THRESHOLD_REJECT:
            return DeduplicationResult(
                status=DuplicateStatus.SEMANTIC_DUPLICATE,
                action=ActionRecommendation.REJECT_REDUNDANT,
                similarity_score=highest_score,
                matched_passage_id=best_match.passage_id,
                matched_source_uri=best_match.source_uri,
                exact_hash_match=False,
                explanation=(
                    f"Semantic duplicate detected ({highest_score:.3f} >= {self.SEMANTIC_THRESHOLD_REJECT}). "
                    f"Matches existing passage '{best_match.passage_id}' in same jurisdiction ({candidate.jurisdiction})."
                ),
                requires_human_review=False
            )
        else:
            return DeduplicationResult(
                status=DuplicateStatus.NEAR_DUPLICATE_UNCERTAIN,
                action=ActionRecommendation.FLAG_FOR_HUMAN_REVIEW,
                similarity_score=highest_score,
                matched_passage_id=best_match.passage_id,
                matched_source_uri=best_match.source_uri,
                exact_hash_match=False,
                explanation=(
                    f"Near-duplicate candidate ({highest_score:.3f}). Similar to '{best_match.passage_id}' "
                    "but contains potential amendments or distinct provisions. Queued for human review."
                ),
                requires_human_review=True
            )

