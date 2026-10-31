from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConfidenceType(str, Enum):
    HEURISTIC = "HEURISTIC"
    MODEL_ESTIMATED = "MODEL_ESTIMATED"
    RULE_DERIVED = "RULE_DERIVED"
    CRYPTOGRAPHIC_INTEGRITY = "CRYPTOGRAPHIC_INTEGRITY"
    EMPIRICALLY_CALIBRATED = "EMPIRICALLY_CALIBRATED"
    UNCALIBRATED = "UNCALIBRATED"


class ConfidenceContract(BaseModel):
    raw_confidence: float = Field(..., ge=0.0, le=1.0)
    calibrated_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_type: str = Field(default=ConfidenceType.RULE_DERIVED.value)
    calibration_status: str = Field(default="HEURISTIC_BOUNDED")  # UNCALIBRATED, HEURISTIC_BOUNDED, EMPIRICALLY_CALIBRATED
    uncertainty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    supporting_evidence_count: int = Field(default=0, ge=0)
    contradicting_evidence_count: int = Field(default=0, ge=0)
    inference_mode: str = Field(default="DETERMINISTIC_RULES")
    model_identifier: str = Field(default="deterministic_rule_engine_v1.2")
    evaluation_dataset_version: Optional[str] = Field(default="benchmark_100_v1.0")


class GroundingDimension(str, Enum):
    SOURCE_AUTHENTICITY = "SOURCE_AUTHENTICITY"
    PASSAGE_INTEGRITY = "PASSAGE_INTEGRITY"
    CITATION_VALIDITY = "CITATION_VALIDITY"
    QUOTATION_ACCURACY = "QUOTATION_ACCURACY"
    SEMANTIC_SUPPORT = "SEMANTIC_SUPPORT"
    LEGAL_ENTAILMENT = "LEGAL_ENTAILMENT"
    FACT_TO_LAW_APPLICABILITY = "FACT_TO_LAW_APPLICABILITY"
    JURISDICTIONAL_VALIDITY = "JURISDICTIONAL_VALIDITY"
    TEMPORAL_VALIDITY = "TEMPORAL_VALIDITY"


class GroundingStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


class ClaimGroundingResult(BaseModel):
    overall_status: str = Field(default=GroundingStatus.VERIFIED.value)
    dimension_statuses: Dict[str, str] = Field(default_factory=dict)
    dimension_scores: Dict[str, float] = Field(default_factory=dict)
    dimension_rationales: Dict[str, str] = Field(default_factory=dict)
    is_fully_grounded: bool = Field(default=True)
    requires_human_review: bool = Field(default=False)
    audit_notes: List[str] = Field(default_factory=list)


class EvidenceRef(BaseModel):
    evidence_id: str = Field(..., description="Stable identifier of evidence passage")
    passage_reference: str = Field(..., description="Statutory or regulatory article reference")
    digest: str = Field(..., description="Cryptographic SHA256 digest of passage text")
    relationship: str = Field(default="SUPPORTS", description="SUPPORTS, REFUTES, or QUALIFIES")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class ClaimOutput(BaseModel):
    id: Optional[str] = None
    claim_text: str = Field(..., description="Verifiable legal proposition or finding")
    claim_type: str = Field(..., description="STATUTORY_INTERPRETATION, FACTUAL_MAPPING, RISK_ASSESSMENT, or EXCEPTION")
    assumptions: List[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_rationale: str = Field(..., description="Empirical basis for confidence separate from LLM self-belief")
    is_supported: bool = Field(default=True)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    source_document_ids: List[str] = Field(default_factory=list, description="IDs of source documents underpinning this claim")
    analysis_engine: str = Field(default="deterministic_rule_engine_v1.2", description="Engine used to derive or verify claim")
    execution_mode: str = Field(default="DETERMINISTIC_RULES", description="LIVE_MODEL, DETERMINISTIC_RULES, or CACHE")
    verification_mode: str = Field(default="MECHANICAL_CITATION_MATCH", description="MECHANICAL_CITATION_MATCH, SEMANTIC_LLM_ASSESSMENT, or UNVERIFIED")
    entailment_disclosure: str = Field(
        default="Mechanical citation and digest verification confirms textual match; does not constitute proof of semantic legal entailment.",
        description="Explicit disclosure that mechanical matching is not legal entailment proof"
    )
    confidence_contract: Optional[ConfidenceContract] = None
    grounding_result: Optional[ClaimGroundingResult] = None


class CounterargumentOutput(BaseModel):
    target_claim_text: str = Field(..., description="Claim or assumption being contested")
    objection: str = Field(..., description="Legal counter-theory, missing fact, or contradictory authority")
    contrary_evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")


class UncertaintyDetail(BaseModel):
    unresolved_question: str
    impact: float = Field(..., ge=0.0, le=1.0, description="Impact on compliance determination")
    uncertainty: float = Field(..., ge=0.0, le=1.0, description="Degree of legal ambiguity")
    research_feasibility: float = Field(..., ge=0.0, le=1.0, description="Feasibility of resolving via targeted bounty")
    priority_score: Optional[float] = None
    recommended_bounty: bool = False


# PRD Section 8.7 Agent output schema
class AgentExecutionOutput(BaseModel):
    agent_id: str
    role: str
    case_id: str
    case_version: int
    claims: List[ClaimOutput] = Field(default_factory=list)
    evidence_refs: List[EvidenceRef] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    counterarguments: List[CounterargumentOutput] = Field(default_factory=list)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty_details: List[UncertaintyDetail] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    model_version: str = Field(default="veridion-engine-v1.0")
    prompt_version: str = Field(default="1.0.0")
    tool_versions: List[str] = Field(default_factory=lambda: ["retrieval_v1", "rule_engine_v1", "crypto_v1"])
    status: str = Field(default="SUCCESS")  # SUCCESS, PARTIAL, ABSTAINED, FAILED
    error_details: Optional[str] = None
    execution_time_ms: Optional[float] = None
    confidence_contract: Optional[ConfidenceContract] = None


class AgentResponse(BaseModel):
    id: str
    wallet_address: str
    role: str
    model_provider_version: str
    prompt_version: str
    status: str
    reputation_score: float
    brier_score: float
    sample_count: int
    simulated_credits: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentReputationResponse(BaseModel):
    agent_id: str
    wallet_address: str
    role: str
    reputation_score: float
    brier_score: float
    sample_count: int
    simulated_credits: float
    scoring_version: str
    is_small_sample: bool
    reputation_weight: float


class ReputationRecordResponse(BaseModel):
    id: str
    agent_id: str
    delta: float
    score_before: float
    score_after: float
    reason: str
    event_reference: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
