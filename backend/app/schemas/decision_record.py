from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceSourceRecord(BaseModel):
    document_id: str
    title: str
    authority: str
    jurisdiction: str
    url: str
    official_identifier: Optional[str] = None
    document_version: str = "1.0"
    publication_date: str
    effective_date: str
    retrieval_timestamp: str
    content_digest: str
    digest_algorithm: str = "SHA-256"
    provenance: str  # REMOTE_OFFICIAL_SOURCE, BUNDLED_FIXTURE, USER_SUBMITTED, DEMO, TEST
    access_classification: str = "PUBLIC_OFFICIAL"


class EvidencePassageRecord(BaseModel):
    passage_id: str
    document_id: str
    passage_reference: str
    content_reference: str
    text_excerpt: str
    passage_digest: str
    digest_algorithm: str = "SHA-256"
    source_version: str = "1.0"
    provenance: str


class ClaimRecord(BaseModel):
    claim_id: str
    agent_id: str
    role: str
    claim_text: str
    claim_type: str  # STATUTORY_INTERPRETATION, FACTUAL_MAPPING, RISK_ASSESSMENT, EXCEPTION
    cited_passage_ids: List[str] = Field(default_factory=list)
    cited_passage_digests: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    confidence: float
    status: str = "SUPPORTED"  # SUPPORTED, CONTESTED, QUALIFIED
    counterarguments: List[Dict[str, Any]] = Field(default_factory=list)
    entailment_disclaimer: str = "Mechanical citation match; formal legal entailment requires human or judicial determination."


class ForecastCommitmentRecord(BaseModel):
    forecast_id: str
    market_id: str
    agent_id: str
    wallet_address: str
    commitment_hash: str
    committed_at: str
    commit_tx_hash: Optional[str] = None
    reveal_status: str  # COMMITTED, REVEALED, MISMATCH, EXPIRED
    revealed_at: Optional[str] = None
    revealed_probability: Optional[float] = None
    revealed_evidence_digest: Optional[str] = None
    revealed_nonce: Optional[str] = None
    reveal_tx_hash: Optional[str] = None
    cryptographic_validity: str = "UNVERIFIED"  # VERIFIED, MISMATCH, UNREVEALED, PENDING


class ForecastMarketRecord(BaseModel):
    market_id: str
    question: str
    outcome_definition: str
    resolution_method: str
    rubric_version: str = "1.0"
    commit_deadline: str
    reveal_deadline: str
    resolution_deadline: str
    scoring_version: str = "brier_v1"
    status: str
    contract_address: str
    evaluator_address: str
    proposed_outcome: Optional[int] = None
    resolution_reference: Optional[str] = None
    aggregate_probability: float = 0.0
    disagreement_variance: float = 0.0
    sample_size: int = 0
    commitments: List[ForecastCommitmentRecord] = Field(default_factory=list)


class SettlementRecord(BaseModel):
    settlement_id: str
    reference_id: str
    participant_address: str
    score: Optional[float] = None
    scoring_method: str = "brier_score"
    reward_credits: float = 0.0
    reward_type: str = "SIMULATED_CREDITS"  # SIMULATED_CREDITS vs ON_CHAIN_TRANSFER
    tx_hash: Optional[str] = None
    settlement_status: str = "CONFIRMED"  # CONFIRMED, PENDING, SIMULATED
    settled_at: str


class AuditEventLink(BaseModel):
    event_id: str
    sequence_number: int
    event_type: str
    actor: str
    payload_digest: str
    previous_event_digest: Optional[str] = None
    event_digest: str
    tx_hash: Optional[str] = None
    timestamp: str


class AnalysisConfiguration(BaseModel):
    orchestration_version: str = "veridion_agent_orchestration_v1.0.0"
    software_version: str = "veridion-core@1.0.0"
    deterministic_rule_version: str = "statutory_rule_engine_v1.0"
    prompt_template_versions: Dict[str, str] = Field(default_factory=dict)
    model_provider_observed: str = "deterministic_simulation_engine"
    inference_parameters: Dict[str, Any] = Field(default_factory=dict)
    reproducibility_notice: str = (
        "Replaying recorded decision outputs verifies historical fidelity and cryptographic provenance. "
        "Re-running nondeterministic model inference is not guaranteed to generate identical textual tokens."
    )


class CanonicalDecisionRecord(BaseModel):
    schema_version: str = "veridion_decision_record_v1.0.0"
    decision_id: str
    case_id: str
    case_version: int = 1
    case_title: str
    case_question: str
    jurisdiction: str
    assessment_date: str
    facts: Dict[str, Any]
    analysis_configuration: AnalysisConfiguration
    analysis_timestamp: str
    evidence_sources: List[EvidenceSourceRecord] = Field(default_factory=list)
    evidence_passages: List[EvidencePassageRecord] = Field(default_factory=list)
    claims: List[ClaimRecord] = Field(default_factory=list)
    forecast_markets: List[ForecastMarketRecord] = Field(default_factory=list)
    settlements: List[SettlementRecord] = Field(default_factory=list)
    audit_events: List[AuditEventLink] = Field(default_factory=list)
    record_digest: Optional[str] = None


class AuditPackageManifest(BaseModel):
    package_id: str
    spec_version: str = "VERIDION_AUDIT_SPEC_V1"
    case_id: str
    generated_at: str
    generator_software: str = "veridion-core@1.0.0"
    decision_record_digest: str
    audit_chain_head_digest: str
    merkle_checkpoint_root: str
    verification_instructions: str
