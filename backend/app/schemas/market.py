from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MarketCreateRequest(BaseModel):
    case_id: str
    question: str = Field(..., description="Binary event question with objective benchmark outcome")
    outcome_definition: str = Field(..., description="Exact definition of 1 (YES) and 0 (NO)")
    resolution_method: str = Field(..., description="Predeclared resolution procedure/rubric")
    rubric_version: str = Field(default="1.0")
    commit_deadline: datetime
    reveal_deadline: datetime
    resolution_deadline: datetime
    challenge_window_seconds: int = Field(default=86400)
    void_criteria: str = Field(..., description="Conditions under which market is voided/unresolved")
    evaluator_address: Optional[str] = None


class MarketCommitRequest(BaseModel):
    agent_id: str
    commitment_hash: str = Field(..., description="keccak256 hash H(chainId, marketId, agentId, prob, digest, nonce)")


class MarketRevealRequest(BaseModel):
    agent_id: str
    probability: float = Field(..., ge=0.0, le=1.0)
    evidence_digest: str = Field(..., description="Digest of evidence supporting the forecast")
    nonce: str = Field(..., description="Secret 32-byte hexadecimal nonce")


class MarketResolveRequest(BaseModel):
    proposed_outcome: int = Field(..., ge=0, le=1, description="1 for YES, 0 for NO")
    resolution_reference: str = Field(..., description="Benchmark evaluation URL or record ID")
    evaluator_address: str


class MarketChallengeRequest(BaseModel):
    challenger_address: str
    reason: str = Field(..., min_length=10)


class ForecastResponse(BaseModel):
    id: str
    market_id: str
    agent_id: str
    commitment_hash: str
    probability: Optional[float]
    evidence_digest: Optional[str]
    nonce: Optional[str]
    reveal_status: str
    commit_tx_hash: Optional[str]
    reveal_tx_hash: Optional[str]
    brier_score: Optional[float]
    created_at: datetime
    revealed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class MarketResponse(BaseModel):
    id: str
    case_id: str
    case_version: int
    question: str
    outcome_definition: str
    resolution_method: str
    rubric_version: str
    commit_deadline: datetime
    reveal_deadline: datetime
    resolution_deadline: datetime
    challenge_window_seconds: int
    scoring_version: str
    void_criteria: str
    status: str
    contract_address: str
    proposed_outcome: Optional[int]
    resolution_reference: Optional[str]
    evaluator_address: str
    aggregate_probability: float
    disagreement_variance: float
    sample_size: int
    created_at: datetime
    forecasts: List[ForecastResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_low_sample(self) -> bool:
        """FR-049: Show low sample state when N < 5."""
        return self.sample_size < 5
