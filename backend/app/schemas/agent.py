from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


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
