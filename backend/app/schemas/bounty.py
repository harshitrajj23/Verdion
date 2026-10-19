from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BountyCreateRequest(BaseModel):
    case_id: str
    question: str = Field(..., description="Narrow research question to be resolved")
    acceptance_criteria: str = Field(..., description="Rubric for evaluating submitted evidence")
    reward_amount: float = Field(default=100.0, gt=0.0, description="Reward in simulated credits")
    deadline: datetime
    challenge_window_seconds: int = Field(default=86400)
    creator_address: Optional[str] = None


class EvidenceSubmissionRequest(BaseModel):
    contributor_address: str
    title: str = Field(..., min_length=3)
    source_reference: str = Field(..., description="Citation or legal authority reference")
    content: str = Field(..., min_length=10, description="Verifiable passage or factual evidence")
    provenance: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BountyChallengeRequest(BaseModel):
    challenger_address: str
    reason: str = Field(..., min_length=10)


class BountySettleRequest(BaseModel):
    winning_submission_id: str
    reviewer_address: str
    review_reason: str = Field(..., min_length=5)


class EvidenceSubmissionResponse(BaseModel):
    id: str
    bounty_id: str
    contributor_address: str
    title: str
    source_reference: str
    content: str
    digest: str
    provenance: Dict[str, Any]
    status: str
    review_reason: Optional[str]
    reviewer_address: Optional[str]
    submitted_at: datetime
    reviewed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class BountyResponse(BaseModel):
    id: str
    case_id: str
    question: str
    acceptance_criteria: str
    reward_amount: float
    deadline: datetime
    challenge_window_seconds: int
    status: str
    contract_reference: str
    winning_submission_id: Optional[str]
    creator_address: str
    created_at: datetime
    submissions: List[EvidenceSubmissionResponse] = []

    model_config = ConfigDict(from_attributes=True)
