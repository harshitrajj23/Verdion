# FENCE RULE:
# Isolation fence markers ([DATA_ONLY_START], [DATA_ONLY_END], and <untrusted_evidence_passage> tags)
# are strictly isolation scaffolding and are never part of a supporting_quote.
# The verifier compares supporting_quote against the canonical passage text in ml/corpus/passages.json,
# not against the fenced text presented to the model.
# If supporting_quote contains any fence marker, the verifier sets evidence_status=UNSUPPORTED with
# reason code QUOTE_HAS_FENCE_MARKER. The verifier never strips markers to accept a quote.

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

FENCE_MARKERS = (
    "[DATA_ONLY_START]",
    "[DATA_ONLY_END]",
    "<untrusted_evidence_passage",
    "</untrusted_evidence_passage>",
)


class ValidationError(Exception):
    """Raised when an agent output or claim does not satisfy the §8.7 schema."""
    pass


@dataclass
class UncertaintyRating:
    score: float
    impact: float
    feasibility: float
    priority: float
    rationale: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UncertaintyRating:
        if not isinstance(data, dict):
            raise ValidationError("uncertainty must be a JSON object")
        for req in ["score", "impact", "feasibility", "priority", "rationale"]:
            if req not in data:
                raise ValidationError(f"Missing required §8.7 uncertainty field: '{req}'")
        try:
            return cls(
                score=float(data["score"]),
                impact=float(data["impact"]),
                feasibility=float(data["feasibility"]),
                priority=float(data["priority"]),
                rationale=str(data["rationale"]),
            )
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid types in uncertainty: {e}") from e


@dataclass
class ClaimOutput:
    id: str
    case_id: str
    case_version: int
    agent_id: str
    claim_text: str
    claim_type: str
    evidence_status: str
    timestamp: str
    evidence_refs: List[str]
    assumptions: List[str]
    supporting_quote: Optional[str] = None
    supporting_passage_id: Optional[str] = None
    supporting_sentence_index: Optional[int] = None
    verifier_notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClaimOutput:
        if not isinstance(data, dict):
            raise ValidationError("claim must be a JSON object")
        for req in [
            "id",
            "case_id",
            "case_version",
            "agent_id",
            "claim_text",
            "claim_type",
            "evidence_status",
            "timestamp",
        ]:
            if req not in data:
                raise ValidationError(f"Missing required claim field: '{req}'")
        valid_types = {
            "LEGAL_INTERPRETATION",
            "FACTUAL_MAPPING",
            "RISK_FINDING",
            "HYPOTHESIS",
            "STATUTORY_REQUIREMENT",
        }
        if data["claim_type"] not in valid_types:
            raise ValidationError(f"Invalid claim_type: '{data['claim_type']}'")
        valid_statuses = {
            "SUPPORTED",
            "UNSUPPORTED",
            "CONTRADICTED",
            "QUALIFIED",
            "UNRESOLVED_APPLICABILITY",
            "ENGINE_CHECKED",
            "MODEL_ESTIMATE",
        }
        if data["evidence_status"] not in valid_statuses:
            raise ValidationError(f"Invalid evidence_status: '{data['evidence_status']}'")
        return cls(
            id=str(data["id"]),
            case_id=str(data["case_id"]),
            case_version=int(data["case_version"]),
            agent_id=str(data["agent_id"]),
            claim_text=str(data["claim_text"]),
            claim_type=str(data["claim_type"]),
            evidence_status=str(data["evidence_status"]),
            timestamp=str(data["timestamp"]),
            evidence_refs=list(data.get("evidence_refs", [])),
            assumptions=list(data.get("assumptions", [])),
            supporting_quote=str(data["supporting_quote"]) if data.get("supporting_quote") else None,
            supporting_passage_id=str(data["supporting_passage_id"]) if data.get("supporting_passage_id") else None,
            supporting_sentence_index=int(data["supporting_sentence_index"]) if "supporting_sentence_index" in data and data["supporting_sentence_index"] is not None else None,
            verifier_notes=str(data["verifier_notes"]) if data.get("verifier_notes") else None,
        )


@dataclass
class AgentOutput:
    agent_id: str
    role: str
    case_id: str
    case_version: int
    claims: List[ClaimOutput]
    evidence_refs: List[str]
    assumptions: List[str]
    counterarguments: List[str]
    uncertainty: UncertaintyRating
    recommended_actions: List[str]
    model_version: str
    prompt_version: str
    tool_versions: List[str]
    status: str
    error_details: Optional[str]

    REQUIRED_FIELDS = (
        "agent_id",
        "role",
        "case_id",
        "case_version",
        "claims",
        "evidence_refs",
        "assumptions",
        "counterarguments",
        "uncertainty",
        "recommended_actions",
        "model_version",
        "prompt_version",
        "tool_versions",
        "status",
        "error_details",
    )

    @classmethod
    def validate_dict(cls, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationError("Agent output must be a dictionary")
        for field in cls.REQUIRED_FIELDS:
            if field not in data:
                raise ValidationError(f"Missing required §8.7 field: '{field}'")
        valid_roles = {
            "LEGAL_RESEARCHER",
            "LEGAL_INTERPRETER",
            "ADVERSARIAL_RESEARCHER",
            "EVIDENCE_VERIFIER",
            "QUANTITATIVE_FORECASTER",
            "COORDINATOR",
        }
        if data["role"] not in valid_roles:
            raise ValidationError(f"Invalid role: '{data['role']}'")
        valid_statuses = {"SUCCESS", "PARTIAL", "FAILED", "ABSTAINED"}
        if data["status"] not in valid_statuses:
            raise ValidationError(f"Invalid status: '{data['status']}'")
        if not isinstance(data["claims"], list):
            raise ValidationError("'claims' must be a list")
        for claim in data["claims"]:
            ClaimOutput.from_dict(claim)
        UncertaintyRating.from_dict(data["uncertainty"])
        for list_field in [
            "evidence_refs",
            "assumptions",
            "counterarguments",
            "recommended_actions",
            "tool_versions",
        ]:
            if not isinstance(data.get(list_field), list):
                raise ValidationError(f"'{list_field}' must be a list")


class SentenceList(list):
    """List of extracted sentences annotated with splitter_version metadata."""

    def __init__(self, sentences: List[str], splitter_version: str = "1.1.0") -> None:
        super().__init__(sentences)
        self.splitter_version = splitter_version
        self.sentences = list(sentences)

    def get(self, key: str, default: Any = None) -> Any:
        if key == "splitter_version":
            return self.splitter_version
        if key == "sentences":
            return self.sentences
        return default

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, str):
            if item == "splitter_version":
                return self.splitter_version
            if item == "sentences":
                return self.sentences
            raise KeyError(item)
        return super().__getitem__(item)


def split_passage_into_sentences(text: str, version: str = "1.1.0") -> SentenceList:
    r"""
    Deterministic sentence splitting rule:
    - Version '1.0.0':
      Primary rule only: split at period followed by whitespace and a capital letter: (?<=\.)\s+(?=[A-Z]).
    - Version '1.1.0':
      Primary rule: split at period followed by whitespace and a capital letter: (?<=\.)\s+(?=[A-Z]).
      Secondary rule: after the period-capital split, any sentence over 60 words is split further
      on ';' followed by whitespace: (?<=;)\s+.
      If a sentence is still over 60 words after the semicolon split, it remains unsplit and the
      verifier flags it SENTENCE_TOO_LONG. We do not split on commas or arbitrary word counts.
    Each extracted sentence is stripped of leading/trailing whitespace,
    preserving exact verbatim punctuation within the sentence.
    """
    if not text or not text.strip():
        return SentenceList([], splitter_version=version)

    clean_text = text.strip()
    primary = [p.strip() for p in re.split(r"(?<=\.)\s+(?=[A-Z])", clean_text) if p.strip()]

    if version == "1.0.0":
        return SentenceList(primary, splitter_version="1.0.0")

    # Version 1.1.0 (default): secondary split on semicolon for sentences over 60 words
    secondary: List[str] = []
    for s in primary:
        if len(s.split()) > 60 and ";" in s:
            parts = [p.strip() for p in re.split(r"(?<=;)\s+", s) if p.strip()]
            secondary.extend(parts)
        else:
            secondary.append(s)

    return SentenceList(secondary, splitter_version="1.1.0")


def validate_researcher_llm_payload(
    data: Dict[str, Any],
    valid_passage_ids: Optional[Set[str]] = None,
    passage_sentences: Optional[Dict[str, List[str]]] = None,
) -> None:
    """Validates the raw parsed LLM response for Legal Researcher role."""
    if not isinstance(data, dict):
        raise ValidationError("LLM response must be a JSON object")
    required = [
        "claims",
        "evidence_refs",
        "assumptions",
        "counterarguments",
        "uncertainty",
        "recommended_actions",
    ]
    for req in required:
        if req not in data:
            raise ValidationError(f"Missing required §8.7 researcher field: '{req}'")
    if not isinstance(data["claims"], list):
        raise ValidationError("'claims' must be a list")

    # Validate citations against valid_passage_ids if provided
    if valid_passage_ids is not None:
        for ref in data.get("evidence_refs", []):
            if ref not in valid_passage_ids:
                raise ValidationError(f"Invalid citation '{ref}' not found in ml/corpus/passages.json")

    for idx, c in enumerate(data["claims"]):
        if not isinstance(c, dict):
            raise ValidationError(f"Claim #{idx+1} must be an object")
        if not c.get("claim_text"):
            raise ValidationError(f"Claim #{idx+1} missing 'claim_text'")

        c_refs = c.get("evidence_refs", [])
        if not isinstance(c_refs, list):
            raise ValidationError(f"Claim #{idx+1} 'evidence_refs' must be a list")

        sup_id = c.get("supporting_passage_id")
        if not sup_id:
            raise ValidationError(f"Claim #{idx+1} missing 'supporting_passage_id'")
        if sup_id not in c_refs:
            raise ValidationError(
                f"Claim #{idx+1} supporting_passage_id '{sup_id}' not in evidence_refs: {c_refs}"
            )

        # Reject any claim_text containing a passage_id other than supporting_passage_id
        claim_text = str(c.get("claim_text", ""))
        found_pids = set(re.findall(r"\bpas_[a-zA-Z0-9_]+\b", claim_text))
        if valid_passage_ids is not None:
            found_pids.update(pid for pid in valid_passage_ids if pid in claim_text)
        for pid in found_pids:
            if pid != sup_id:
                raise ValidationError(
                    f"Claim #{idx+1} claim_text references '{pid}' which is not its supporting_passage_id '{sup_id}'"
                )

        if "supporting_sentence_index" not in c or not isinstance(c.get("supporting_sentence_index"), int) or isinstance(c.get("supporting_sentence_index"), bool):
            raise ValidationError(f"Claim #{idx+1} missing or non-integer 'supporting_sentence_index'")

        sent_idx = c["supporting_sentence_index"]
        if passage_sentences is not None and sup_id in passage_sentences:
            sents = passage_sentences[sup_id]
            if sent_idx < 0 or sent_idx >= len(sents):
                raise ValidationError(
                    f"Claim #{idx+1} supporting_sentence_index {sent_idx} out of range for passage '{sup_id}' (available indices: 0 to {len(sents)-1})"
                )

        if valid_passage_ids is not None:
            for ref in c_refs:
                if ref not in valid_passage_ids:
                    raise ValidationError(f"Claim #{idx+1} invalid citation '{ref}' not found in ml/corpus/passages.json")

    # Validate uncertainty fields
    u = data.get("uncertainty")
    if not isinstance(u, dict):
        raise ValidationError("uncertainty must be a JSON object")
    for u_req in ["score", "impact", "feasibility", "rationale"]:
        if u_req not in u:
            raise ValidationError(f"Missing required uncertainty field: '{u_req}'")


def validate_interpreter_llm_payload(
    data: Dict[str, Any],
    allowed_passage_ids: Optional[Set[str]] = None,
    passage_sentences: Optional[Dict[str, List[str]]] = None,
) -> None:
    """Validates the raw parsed LLM response for Legal Interpreter role."""
    if not isinstance(data, dict):
        raise ValidationError("LLM response must be a JSON object")
    required = ["claims", "assumptions", "counterarguments", "uncertainty", "recommended_actions"]
    for req in required:
        if req not in data:
            raise ValidationError(f"Missing required interpreter field: '{req}'")
    if not isinstance(data["claims"], list):
        raise ValidationError("'claims' must be a list")

    for idx, c in enumerate(data["claims"]):
        if not isinstance(c, dict):
            raise ValidationError(f"Claim #{idx+1} must be an object")
        if not c.get("claim_text"):
            raise ValidationError(f"Claim #{idx+1} missing 'claim_text'")

        sup_id = c.get("supporting_passage_id")
        if sup_id:
            if allowed_passage_ids is not None and sup_id not in allowed_passage_ids:
                raise ValidationError(
                    f"Claim #{idx+1} cites '{sup_id}' which is not in the supported researcher citations: {allowed_passage_ids}"
                )
            if "supporting_sentence_index" in c and c["supporting_sentence_index"] is not None:
                sent_idx = c["supporting_sentence_index"]
                if not isinstance(sent_idx, int) or isinstance(sent_idx, bool):
                    raise ValidationError(f"Claim #{idx+1} supporting_sentence_index must be an integer")
                if passage_sentences is not None and sup_id in passage_sentences:
                    sents = passage_sentences[sup_id]
                    if sent_idx < 0 or sent_idx >= len(sents):
                        raise ValidationError(
                            f"Claim #{idx+1} supporting_sentence_index {sent_idx} out of range for '{sup_id}'"
                        )

    u = data.get("uncertainty")
    if not isinstance(u, dict):
        raise ValidationError("uncertainty must be a JSON object")
    for u_req in ["score", "impact", "feasibility", "rationale"]:
        if u_req not in u:
            raise ValidationError(f"Missing required uncertainty field: '{u_req}'")


def validate_adversarial_llm_payload(
    data: Dict[str, Any],
    valid_passage_ids: Optional[Set[str]] = None,
    passage_sentences: Optional[Dict[str, List[str]]] = None,
) -> None:
    """Validates the raw parsed LLM response for Adversarial Researcher role."""
    if not isinstance(data, dict):
        raise ValidationError("LLM response must be a JSON object")
    required = ["claims", "assumptions", "counterarguments", "uncertainty", "recommended_actions"]
    for req in required:
        if req not in data:
            raise ValidationError(f"Missing required adversarial field: '{req}'")
    if not isinstance(data["claims"], list):
        raise ValidationError("'claims' must be a list")

    for idx, c in enumerate(data["claims"]):
        if not isinstance(c, dict):
            raise ValidationError(f"Claim #{idx+1} must be an object")
        if not c.get("claim_text"):
            raise ValidationError(f"Claim #{idx+1} missing 'claim_text'")

        sup_id = c.get("supporting_passage_id")
        if not sup_id:
            raise ValidationError(f"Claim #{idx+1} missing 'supporting_passage_id'")
        if valid_passage_ids is not None and sup_id not in valid_passage_ids:
            raise ValidationError(f"Claim #{idx+1} cited passage '{sup_id}' not in corpus")

        if "supporting_sentence_index" not in c or not isinstance(c["supporting_sentence_index"], int) or isinstance(c["supporting_sentence_index"], bool):
            raise ValidationError(f"Claim #{idx+1} missing or non-integer 'supporting_sentence_index'")

        sent_idx = c["supporting_sentence_index"]
        if passage_sentences is not None and sup_id in passage_sentences:
            sents = passage_sentences[sup_id]
            if sent_idx < 0 or sent_idx >= len(sents):
                raise ValidationError(
                    f"Claim #{idx+1} supporting_sentence_index {sent_idx} out of range for '{sup_id}'"
                )

    u = data.get("uncertainty")
    if not isinstance(u, dict):
        raise ValidationError("uncertainty must be a JSON object")
    for u_req in ["score", "impact", "feasibility", "rationale"]:
        if u_req not in u:
            raise ValidationError(f"Missing required uncertainty field: '{u_req}'")


def validate_forecaster_llm_payload(data: Dict[str, Any]) -> None:
    """Validates the raw parsed LLM response for Quantitative Forecaster role."""
    if not isinstance(data, dict):
        raise ValidationError("LLM response must be a JSON object")
    if "forecast" not in data:
        raise ValidationError("Missing required 'forecast' object in forecaster response")

    forecast = data["forecast"]
    if not isinstance(forecast, dict):
        raise ValidationError("'forecast' must be a JSON object")

    if forecast.get("abstain") is True:
        # Valid abstention
        return

    prob = forecast.get("probability")
    if prob is None or not isinstance(prob, (int, float)) or isinstance(prob, bool):
        raise ValidationError(f"Forecaster probability '{prob}' must be a float between 0.0 and 1.0 or abstain=true")
    if not (0.0 <= float(prob) <= 1.0):
        raise ValidationError(f"Forecaster probability {prob} out of range [0.0, 1.0]")

    ev_def = forecast.get("event_definition")
    if not ev_def or not isinstance(ev_def, str) or not ev_def.strip():
        raise ValidationError("Forecaster 'event_definition' must be a non-empty string")

    u = data.get("uncertainty")
    if not isinstance(u, dict):
        raise ValidationError("uncertainty must be a JSON object")
    for u_req in ["score", "impact", "feasibility", "rationale"]:
        if u_req not in u:
            raise ValidationError(f"Missing required uncertainty field: '{u_req}'")


def verify_claim_quote(
    evidence_refs: List[str],
    supporting_quote: Optional[str],
    supporting_passage_id: Optional[str],
    passage_lookup: Dict[str, Dict[str, Any]],
    supporting_sentence_index: Optional[int] = None,
) -> tuple[str, Optional[str]]:
    """Verifies quote-span and sentence-index support for a legal claim.

    Rules per Stage 2B-1 Redesign:
    - SUPPORTED only if: every evidence_ref exists in passages.json AND supporting_passage_id is in evidence_refs
      AND supporting_passage_id exists in passages.json AND supporting_sentence_index is in range (if specified)
      AND supporting_quote is non-empty, contains no fence markers, does not exceed 60 words,
      and appears verbatim (after whitespace normalization) in the passage named by supporting_passage_id.
    - UNSUPPORTED otherwise, recording reason code from:
      NOT_IN_EVIDENCE_REFS, PASSAGE_NOT_FOUND, INDEX_OUT_OF_RANGE, QUOTE_EMPTY, QUOTE_HAS_FENCE_MARKER,
      QUOTE_NOT_VERBATIM, SENTENCE_TOO_LONG.

    LIMIT OF VERIFIER:
    SUPPORTED means the cited sentence exists in the named passage.
    It does not establish that the sentence supports the claim. That check is a human review step (PRD §8.4, §17.4).
    """
    if not supporting_passage_id or supporting_passage_id not in evidence_refs:
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=NOT_IN_EVIDENCE_REFS"

    if not evidence_refs or any(ref not in passage_lookup for ref in evidence_refs) or supporting_passage_id not in passage_lookup:
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=PASSAGE_NOT_FOUND"

    named_passage = passage_lookup.get(supporting_passage_id)
    if not named_passage:
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=PASSAGE_NOT_FOUND"

    passage_sentences = split_passage_into_sentences(named_passage.get("content", ""))
    if supporting_sentence_index is not None:
        if (
            not isinstance(supporting_sentence_index, int)
            or isinstance(supporting_sentence_index, bool)
            or supporting_sentence_index < 0
            or supporting_sentence_index >= len(passage_sentences)
        ):
            return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=INDEX_OUT_OF_RANGE"

    if not supporting_quote or not str(supporting_quote).strip():
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=QUOTE_EMPTY"

    raw_quote = str(supporting_quote).strip()

    if any(marker in raw_quote for marker in FENCE_MARKERS):
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=QUOTE_HAS_FENCE_MARKER"

    norm_quote = " ".join(raw_quote.split()).strip('"\'')
    if not norm_quote:
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=QUOTE_EMPTY"

    # Hard limit on sentence length: at most 60 words (Stage 2B-1 Redesign)
    if len(norm_quote.split()) > 60:
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=SENTENCE_TOO_LONG"

    passage_content = " ".join(named_passage.get("content", "").split())
    if norm_quote in passage_content or norm_quote.lower() in passage_content.lower():
        return "SUPPORTED", None
    else:
        return "UNSUPPORTED", f"supporting_passage_id={supporting_passage_id}, match=false, reason=QUOTE_NOT_VERBATIM"
