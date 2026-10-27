from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    jurisdiction = Column(String(64), nullable=False, index=True)
    assessment_date = Column(String(32), nullable=False)
    facts = Column(JSON, nullable=False, default=dict)
    scope_version = Column(Integer, default=1, nullable=False)
    status = Column(String(32), default="DRAFT", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    claims = relationship("Claim", back_populates="case", cascade="all, delete-orphan")
    markets = relationship("PredictionMarket", back_populates="case", cascade="all, delete-orphan")
    bounties = relationship("EvidenceBounty", back_populates="case", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="case", cascade="all, delete-orphan")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    authority = Column(String(255), nullable=False)
    jurisdiction = Column(String(64), nullable=False, index=True)
    url = Column(String(512), nullable=False)
    publication_date = Column(String(32), nullable=False)
    effective_date = Column(String(32), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    digest = Column(String(66), nullable=False)
    version = Column(String(32), nullable=False, default="1.0")
    raw_content = Column(Text, nullable=False)

    passages = relationship("EvidencePassage", back_populates="document", cascade="all, delete-orphan")


class EvidencePassage(Base):
    __tablename__ = "evidence_passages"

    id = Column(String(64), primary_key=True, index=True)
    document_id = Column(String(64), ForeignKey("source_documents.id"), nullable=False, index=True)
    passage_reference = Column(String(128), nullable=False)
    content_reference = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    digest = Column(String(66), nullable=False)
    source_version = Column(String(32), nullable=False, default="1.0")

    document = relationship("SourceDocument", back_populates="passages")
    claim_links = relationship("ClaimEvidenceLink", back_populates="evidence")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)
    wallet_address = Column(String(42), nullable=False, unique=True, index=True)
    role = Column(String(64), nullable=False, index=True)
    model_provider_version = Column(String(64), nullable=False)
    prompt_version = Column(String(32), nullable=False, default="1.0")
    status = Column(String(32), default="ACTIVE", nullable=False)
    reputation_score = Column(Float, default=100.0, nullable=False)
    brier_score = Column(Float, default=0.25, nullable=False)
    sample_count = Column(Integer, default=0, nullable=False)
    simulated_credits = Column(Float, default=1000.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    claims = relationship("Claim", back_populates="agent")
    forecasts = relationship("Forecast", back_populates="agent")


class Claim(Base):
    __tablename__ = "claims"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    case_version = Column(Integer, nullable=False, default=1)
    agent_id = Column(String(64), ForeignKey("agents.id"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(64), nullable=False)  # STATUTORY_INTERPRETATION, FACTUAL_MAPPING, RISK_ASSESSMENT, EXCEPTION
    assumptions = Column(JSON, nullable=False, default=list)
    confidence_metadata = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), default="SUPPORTED", nullable=False)  # SUPPORTED, UNSUPPORTED, CONTESTED
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("Case", back_populates="claims")
    agent = relationship("Agent", back_populates="claims")
    evidence_links = relationship("ClaimEvidenceLink", back_populates="claim", cascade="all, delete-orphan")


class ClaimEvidenceLink(Base):
    __tablename__ = "claim_evidence_links"

    id = Column(String(64), primary_key=True, index=True)
    claim_id = Column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    evidence_id = Column(String(64), ForeignKey("evidence_passages.id"), nullable=False, index=True)
    relationship_type = Column(String(32), default="SUPPORTS", nullable=False)  # SUPPORTS, REFUTES, QUALIFIES
    verification_status = Column(String(32), default="VERIFIED", nullable=False)  # VERIFIED, UNVERIFIED, FAILED

    claim = relationship("Claim", back_populates="evidence_links")
    evidence = relationship("EvidencePassage", back_populates="claim_links")


class ArgumentEdge(Base):
    __tablename__ = "argument_edges"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    source_claim_id = Column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    target_claim_id = Column(String(64), ForeignKey("claims.id"), nullable=False, index=True)
    relationship_type = Column(String(32), nullable=False)  # SUPPORTS, CONTRADICTS, QUALIFIES, DEPENDS_ON, SUPERSEDES
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class PredictionMarket(Base):
    __tablename__ = "prediction_markets"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    case_version = Column(Integer, nullable=False, default=1)
    question = Column(Text, nullable=False)
    outcome_definition = Column(Text, nullable=False)
    resolution_method = Column(String(255), nullable=False)
    rubric_version = Column(String(32), nullable=False, default="1.0")
    commit_deadline = Column(DateTime(timezone=True), nullable=False)
    reveal_deadline = Column(DateTime(timezone=True), nullable=False)
    resolution_deadline = Column(DateTime(timezone=True), nullable=False)
    challenge_window_seconds = Column(Integer, default=86400, nullable=False)
    scoring_version = Column(String(32), default="brier_v1", nullable=False)
    void_criteria = Column(Text, nullable=False)
    status = Column(String(32), default="DRAFT", nullable=False, index=True)  # DRAFT, PUBLISHED, REVEAL, CLOSED, RESOLUTION_PROPOSED, CHALLENGE, SETTLED, VOID
    contract_address = Column(String(42), nullable=False)
    proposed_outcome = Column(Integer, nullable=True)  # 0 or 1
    resolution_reference = Column(String(255), nullable=True)
    evaluator_address = Column(String(42), nullable=False)
    aggregate_probability = Column(Float, default=0.0, nullable=False)
    disagreement_variance = Column(Float, default=0.0, nullable=False)
    sample_size = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("Case", back_populates="markets")
    forecasts = relationship("Forecast", back_populates="market", cascade="all, delete-orphan", lazy="selectin")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String(64), primary_key=True, index=True)
    market_id = Column(String(64), ForeignKey("prediction_markets.id"), nullable=False, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id"), nullable=False, index=True)
    commitment_hash = Column(String(66), nullable=False, index=True)
    probability = Column(Float, nullable=True)
    evidence_digest = Column(String(66), nullable=True)
    nonce = Column(String(66), nullable=True)
    reveal_status = Column(String(32), default="COMMITTED", nullable=False)  # COMMITTED, REVEALED, MISMATCH, EXPIRED
    commit_tx_hash = Column(String(66), nullable=True)
    reveal_tx_hash = Column(String(66), nullable=True)
    brier_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    revealed_at = Column(DateTime(timezone=True), nullable=True)

    market = relationship("PredictionMarket", back_populates="forecasts")
    agent = relationship("Agent", back_populates="forecasts")


class EvidenceBounty(Base):
    __tablename__ = "evidence_bounties"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    acceptance_criteria = Column(Text, nullable=False)
    reward_amount = Column(Float, default=100.0, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    challenge_window_seconds = Column(Integer, default=86400, nullable=False)
    status = Column(String(32), default="CREATED", nullable=False, index=True)  # CREATED, FUNDED, OPEN, REVIEW, CHALLENGE, AWARDED, REJECTED, CANCELLED, SETTLED
    contract_reference = Column(String(42), nullable=False)
    winning_submission_id = Column(String(64), nullable=True)
    creator_address = Column(String(42), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("Case", back_populates="bounties")
    submissions = relationship("EvidenceSubmission", back_populates="bounty", cascade="all, delete-orphan", lazy="selectin")


class EvidenceSubmission(Base):
    __tablename__ = "evidence_submissions"

    id = Column(String(64), primary_key=True, index=True)
    bounty_id = Column(String(64), ForeignKey("evidence_bounties.id"), nullable=False, index=True)
    contributor_address = Column(String(42), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    source_reference = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    digest = Column(String(66), nullable=False)
    provenance = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), default="SUBMITTED", nullable=False)  # SUBMITTED, UNDER_REVIEW, ACCEPTED, REJECTED, CHALLENGED
    review_reason = Column(Text, nullable=True)
    reviewer_address = Column(String(42), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    bounty = relationship("EvidenceBounty", back_populates="submissions")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(String(64), primary_key=True, index=True)
    reference_type = Column(String(32), nullable=False)  # MARKET, BOUNTY
    reference_id = Column(String(64), nullable=False, index=True)
    participant_address = Column(String(42), nullable=False, index=True)
    score = Column(Float, nullable=True)
    reward = Column(Float, default=0.0, nullable=False)
    resolution_reference = Column(String(255), nullable=False)
    tx_hash = Column(String(66), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # CASE_CREATED, ANALYSIS_STARTED, AGENT_OUTPUT, MARKET_CREATED, COMMITMENT_SUBMITTED, REVEAL_RECORDED, RESOLUTION_PROPOSED, BOUNTY_SETTLED, etc.
    actor = Column(String(64), nullable=False)
    payload_digest = Column(String(66), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    tx_hash = Column(String(66), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    case = relationship("Case", back_populates="audit_events")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False, index=True)
    status = Column(String(32), default="QUEUED", nullable=False, index=True)  # QUEUED, RUNNING, COMPLETED, FAILED
    retries = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_details = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ReputationRecord(Base):
    __tablename__ = "reputation_records"

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), ForeignKey("agents.id"), nullable=False, index=True)
    delta = Column(Float, nullable=False)
    score_before = Column(Float, nullable=False)
    score_after = Column(Float, nullable=False)
    reason = Column(String(255), nullable=False)
    event_reference = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    tx_hash = Column(String(66), primary_key=True, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    event_name = Column(String(64), nullable=False)
    sender = Column(String(42), nullable=False)
    case_id = Column(String(64), nullable=True, index=True)
    status = Column(String(32), default="CONFIRMED", nullable=False, index=True)  # PENDING, CONFIRMED, REVERTED, UNKNOWN
    block_number = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

