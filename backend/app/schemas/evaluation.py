from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BenchmarkScenario(BaseModel):
    id: str
    title: str
    jurisdiction: str
    question: str
    facts: Dict[str, Any]
    ground_truth_issues: List[str]
    ground_truth_gap_outcome: int = Field(..., ge=0, le=1)  # 1 if compliance gap exists, 0 if fully compliant
    rubric: str = Field(default="Standard regulatory compliance evaluation rubric")
    split: Optional[str] = "TEST"
    legal_instrument: Optional[str] = None
    legal_provision: Optional[str] = None
    expected_counterarguments: List[str] = Field(default_factory=list)
    expected_uncertainty: Optional[float] = None
    provenance: Optional[str] = None
    dataset_version: Optional[str] = None


class BaselineRunResult(BaseModel):
    baseline_name: str  # "BASELINE_A_SINGLE_AGENT", "BASELINE_B_MULTI_AGENT", "VERIDION_PROTOCOL"
    scenario_id: str
    detected_issues: List[str]
    issue_recall: float
    predicted_probability: float
    brier_score: float
    citation_validity: float
    unsupported_claim_rate: float
    execution_time_ms: float
    passed: bool


class BenchmarkSummary(BaseModel):
    total_scenarios: int
    evaluated_at: str
    metrics: Dict[str, Dict[str, float]]
    results: List[BaselineRunResult]
