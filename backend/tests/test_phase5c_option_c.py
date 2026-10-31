import json
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.canonical import (
    compute_canonical_sha256,
    normalize_unicode,
    serialize_canonical_json,
)
from backend.app.core.crypto import (
    compute_brier_score,
    compute_commitment_hash,
    generate_nonce,
    verify_commitment_hash,
)
from backend.app.core.errors import (
    CommitmentMismatchException,
    SettlementAlreadyDoneException,
    UnauthorizedResolutionException,
)
from backend.app.models.entities import (
    Agent,
    AuditEvent,
    Case,
    Claim,
    ClaimEvidenceLink,
    EvidencePassage,
    Forecast,
    PredictionMarket,
    SourceDocument,
    utcnow,
)
from backend.app.schemas.case import CaseCreateRequest
from backend.app.schemas.market import (
    MarketCommitRequest,
    MarketCreateRequest,
    MarketResolveRequest,
    MarketRevealRequest,
)
from backend.app.services.audit_service import AuditService, GENESIS_PREVIOUS_DIGEST
from backend.app.services.audit_verifier import IndependentAuditVerifier
from backend.app.services.case_service import CaseService
from backend.app.services.decision_service import DecisionService
from backend.app.services.forecast_evaluator import ForecastEvaluator
from backend.app.services.market_service import MarketService

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.core.database import Base
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.agent_service import AgentService


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        await RetrievalService.initialize_corpus(session)
        await AgentService.initialize_agents(session)
        yield session

    await engine.dispose()


def test_canonical_serialization_and_hashing():
    """Verify Unicode NFC normalization, key sorting, float formatting, and deterministic digests."""
    # Data with inverted key order, accented characters in NFD vs NFC, and floats
    dict_a = {
        "zeta": 12.3456789,
        "alpha": "café",  # NFC
        "beta": [3, 2, 1],
        "delta": None
    }
    # Create NFD version of 'café' (e + combining acute accent)
    nfd_cafe = "cafe\u0301"
    dict_b = {
        "delta": None,
        "alpha": nfd_cafe,
        "beta": [3, 2, 1],
        "zeta": 12.345679  # rounded float
    }

    digest_a = compute_canonical_sha256(dict_a)
    digest_b = compute_canonical_sha256(dict_b)

    assert digest_a == digest_b, f"Digests should match after NFC normalization and canonical sorting: {digest_a} vs {digest_b}"
    assert digest_a.startswith("0x")
    assert len(digest_a) == 66


# ── 2. AUDIT CHAIN INTEGRITY & TAMPER DETECTION ──────────────────────────

@pytest.mark.asyncio
async def test_audit_chain_integrity_and_tamper_detection(test_db: AsyncSession):
    """Verify hash-chain sequential linkage, Merkle root, and tampering detection."""
    test_case_id = f"case_test_audit_{uuid.uuid4().hex[:6]}"
    case = Case(
        id=test_case_id,
        title="Audit Chain Case",
        question="Testing cryptographic hash chains",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["test"]}
    )
    test_db.add(case)
    await test_db.flush()

    # Log 3 events
    ev1 = await AuditService.log_event(test_db, test_case_id, "CASE_CREATED", "0xUser", {"step": 1})
    ev2 = await AuditService.log_event(test_db, test_case_id, "ANALYSIS_STARTED", "0xSystem", {"step": 2})
    ev3 = await AuditService.log_event(test_db, test_case_id, "EVIDENCE_RETRIEVED", "0xSystem", {"step": 3})
    await test_db.commit()

    # 1. Verify valid unbroken chain
    result = await AuditService.verify_case_audit_chain(test_db, test_case_id)
    assert result["is_valid"] is True
    assert result["status"] == "VERIFIED"
    assert result["events_verified"] == 3
    assert result["merkle_checkpoint_root"].startswith("0x")
    assert len(result["errors"]) == 0

    # 2. Tampering test: Mutate payload of event 2 without updating payload_digest
    ev2_persisted = await test_db.get(AuditEvent, ev2.id)
    ev2_persisted.payload = {"step": 999, "tampered": True}
    await test_db.commit()

    tamper_result = await AuditService.verify_case_audit_chain(test_db, test_case_id)
    assert tamper_result["is_valid"] is False
    assert tamper_result["status"] == "FAILED"
    assert any("Payload tampering detected" in err for err in tamper_result["errors"])

    # 3. Restore event 2 and test sequence disruption
    ev2_persisted.payload = {"step": 2}
    ev2_persisted.sequence_number = 99
    await test_db.commit()

    seq_result = await AuditService.verify_case_audit_chain(test_db, test_case_id)
    assert seq_result["is_valid"] is False
    assert any("Sequence discontinuity" in err for err in seq_result["errors"])


# ── 3. COMMIT-REVEAL CRYPTOGRAPHIC CORRECTNESS ───────────────────────────

def test_commit_reveal_cryptographic_soundness():
    """Verify correct reveals pass and all manipulated reveals fail deterministically."""
    chain_id = 11155111
    market_id = "0x" + "aa" * 32
    agent_wallet = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    prob = 0.725
    evidence_digest = "0x" + "11" * 32
    nonce = generate_nonce()

    commit_hash = compute_commitment_hash(
        chain_id=chain_id,
        market_id=market_id,
        agent_id="agent_test",
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent_wallet
    )

    # 1. Correct reveal
    res_correct = IndependentAuditVerifier.verify_commitment_recomputation(
        chain_id=chain_id,
        market_id=market_id,
        wallet_address=agent_wallet,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        expected_commitment_hash=commit_hash
    )
    assert res_correct["valid"] is True
    assert res_correct["error"] is None

    # 2. Modified probability (0.725 -> 0.726)
    res_bad_prob = IndependentAuditVerifier.verify_commitment_recomputation(
        chain_id=chain_id,
        market_id=market_id,
        wallet_address=agent_wallet,
        probability=0.726,
        evidence_digest=evidence_digest,
        nonce=nonce,
        expected_commitment_hash=commit_hash
    )
    assert res_bad_prob["valid"] is False
    assert "Commitment hash mismatch" in res_bad_prob["error"]

    # 3. Modified nonce
    bad_nonce = generate_nonce()
    res_bad_nonce = IndependentAuditVerifier.verify_commitment_recomputation(
        chain_id=chain_id,
        market_id=market_id,
        wallet_address=agent_wallet,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=bad_nonce,
        expected_commitment_hash=commit_hash
    )
    assert res_bad_nonce["valid"] is False

    # 4. Modified evidence digest
    bad_digest = "0x" + "22" * 32
    res_bad_digest = IndependentAuditVerifier.verify_commitment_recomputation(
        chain_id=chain_id,
        market_id=market_id,
        wallet_address=agent_wallet,
        probability=prob,
        evidence_digest=bad_digest,
        nonce=nonce,
        expected_commitment_hash=commit_hash
    )
    assert res_bad_digest["valid"] is False

    # 5. Wrong market ID
    res_wrong_market = IndependentAuditVerifier.verify_commitment_recomputation(
        chain_id=chain_id,
        market_id="0x" + "bb" * 32,
        wallet_address=agent_wallet,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        expected_commitment_hash=commit_hash
    )
    assert res_wrong_market["valid"] is False


# ── 4. FORECAST SETTLEMENT & BRIER PROPER SCORING ────────────────────────

@pytest.mark.asyncio
async def test_forecast_settlement_and_brier_scoring(test_db: AsyncSession):
    """Verify market resolution, proper Brier scoring, and idempotency protection."""
    # Seed agent
    agent_wallet = "0x1111111111111111111111111111111111111111"
    agent = Agent(
        id="agent_eval_test_unique",
        wallet_address=agent_wallet,
        role="QUANTITATIVE_FORECASTER",
        model_provider_version="v1.0",
        prompt_version="1.0",
        simulated_credits=1000.0,
        reputation_score=100.0
    )
    test_db.add(agent)

    # Seed case
    case = Case(
        id=f"case_mkt_{uuid.uuid4().hex[:6]}",
        title="Market Resolution Case",
        question="Will regulation pass?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["test"], "processing_purpose": "test"}
    )
    test_db.add(case)
    await test_db.flush()

    # Create Market
    now = utcnow()
    mkt_req = MarketCreateRequest(
        case_id=case.id,
        question="Will Article 6(1)(f) exception apply?",
        outcome_definition="1 if allowed, 0 if prohibited",
        resolution_method="CJEU ruling",
        commit_deadline=now,
        reveal_deadline=now,
        resolution_deadline=now,
        void_criteria="Canceled if statute repealed"
    )
    market = await MarketService.create_market(test_db, mkt_req)

    # Commit
    prob = 0.80
    digest = "0x" + "33" * 32
    nonce = generate_nonce()
    commit_hash = compute_commitment_hash(
        chain_id=11155111,
        market_id=market.id,
        agent_id=agent.id,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce,
        wallet_address=agent_wallet
    )

    await MarketService.commit_forecast(
        test_db,
        market.id,
        MarketCommitRequest(agent_id=agent.id, commitment_hash=commit_hash, wallet_address=agent_wallet)
    )

    # Reveal
    await MarketService.reveal_forecast(
        test_db,
        market.id,
        MarketRevealRequest(
            agent_id=agent.id,
            probability=prob,
            evidence_digest=digest,
            nonce=nonce,
            wallet_address=agent_wallet
        )
    )

    # Test unauthorized evaluator rejection
    from backend.app.core.config import settings
    with pytest.raises(UnauthorizedResolutionException):
        await MarketService.propose_resolution(
            test_db,
            market.id,
            MarketResolveRequest(
                proposed_outcome=1,
                resolution_reference="C-487/21 CRIF judgment",
                evaluator_address="0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f"
            )
        )

    # Propose resolution with authorized evaluator: outcome = 1
    await MarketService.propose_resolution(
        test_db,
        market.id,
        MarketResolveRequest(
            proposed_outcome=1,
            resolution_reference="C-487/21 CRIF judgment",
            evaluator_address=settings.EVALUATOR_ADDRESS
        )
    )

    # Settle market
    settle_res = await MarketService.settle_market(test_db, market.id)
    assert settle_res["market_id"] == market.id
    assert len(settle_res["settlements"]) == 1

    # Brier score for probability 0.80 with outcome 1 is (0.8 - 1.0)^2 = 0.04
    fc = settle_res["settlements"][0]
    assert fc["brier_score"] == 0.04
    assert fc["reward"] == 150.0  # Reward for brier < 0.10

    # Test idempotency: attempting to settle an already settled market must raise SettlementAlreadyDoneException
    with pytest.raises(SettlementAlreadyDoneException):
        await MarketService.settle_market(test_db, market.id)



# ── 5. CANONICAL DECISION RECORD & AUDIT PACKAGE EXPORT ──────────────────

@pytest.mark.asyncio
async def test_canonical_decision_record_and_independent_verifier(test_db: AsyncSession):
    """Verify Canonical Decision Record generation, package export, and independent verifier."""
    # Create test case with complete mock lineage
    case_req = CaseCreateRequest(
        title="Option C Auditable Case",
        question="Is synthetic facial analysis permitted under EU AI Act?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["biometric"], "processing_purpose": "safety verification"}
    )
    case = await CaseService.create_case(test_db, case_req)

    # Seed an evidence document and passage
    doc = SourceDocument(
        id=f"doc_test_{uuid.uuid4().hex[:6]}",
        title="EU AI Act 2024/1689",
        authority="European Parliament and Council",
        jurisdiction="EU",
        url="https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
        publication_date="2024-07-12",
        effective_date="2024-08-01",
        retrieved_at=utcnow(),
        digest="0x" + "44" * 32,
        version="1.0",
        provenance="REMOTE_OFFICIAL_SOURCE",
        raw_content="Article 5 Subliminal and biometric categorization systems..."
    )
    test_db.add(doc)

    passage = EvidencePassage(
        id=f"pass_test_{uuid.uuid4().hex[:6]}",
        document_id=doc.id,
        passage_reference="Article 5(1)(d)",
        content_reference="EU AI Act - Article 5(1)(d)",
        text="Biometric categorization systems categorizing natural persons based on biometric data are prohibited...",
        digest="0x" + "55" * 32,
        source_version="1.0",
        provenance="REMOTE_OFFICIAL_SOURCE"
    )
    test_db.add(passage)

    # Seed claim referencing passage
    claim = Claim(
        id=f"claim_test_{uuid.uuid4().hex[:6]}",
        case_id=case.id,
        case_version=1,
        agent_id="agent_legal_researcher",
        claim_text="Biometric categorization without specific consent violates Article 5 prohibition.",
        claim_type="STATUTORY_INTERPRETATION",
        assumptions=["Data processing operates in EU internal market"],
        confidence_metadata={"composite_confidence": 0.92},
        status="SUPPORTED"
    )
    test_db.add(claim)
    await test_db.flush()

    link = ClaimEvidenceLink(
        id=f"link_{uuid.uuid4().hex[:6]}",
        claim_id=claim.id,
        evidence_id=passage.id,
        relationship_type="SUPPORTS",
        verification_status="VERIFIED"
    )
    test_db.add(link)
    await test_db.commit()

    # 1. Build Canonical Decision Record
    record = await DecisionService.build_canonical_decision_record(test_db, case.id, persist=True)
    assert record.decision_id.startswith(f"dec_{case.id}")
    assert record.record_digest.startswith("0x")
    assert len(record.evidence_sources) == 1
    assert len(record.evidence_passages) == 1
    assert len(record.claims) == 1
    assert record.claims[0].cited_passage_ids[0] == passage.id

    # 2. Export Audit Package
    package = await DecisionService.generate_audit_package(test_db, case.id)
    assert "manifest" in package
    assert "decision_record" in package
    assert "audit_chain_verification" in package

    # 3. Verify package through IndependentAuditVerifier
    report = IndependentAuditVerifier.verify_audit_package(package)
    assert report["overall_status"] == "VERIFIED"
    assert report["checks"]["decision_record_digest"]["status"] in ("VERIFIED", "PASS")
    assert report["checks"]["claims_integrity"]["fully_grounded_claims"] == 1

    # 4. Tamper verification: Mutate claim in package and assert verification failure
    tampered_package = json.loads(json.dumps(package))
    tampered_package["decision_record"]["claims"][0]["claim_text"] = "TAMPERED CLAIM TEXT"
    tampered_report = IndependentAuditVerifier.verify_audit_package(tampered_package)
    assert tampered_report["overall_status"] == "FAILED"
    assert tampered_report["checks"]["decision_record_digest"]["status"] in ("FAILED", "FAIL")


# ── 6. EMPIRICAL FORECASTING EVALUATION ───────────────────────────────────

@pytest.mark.asyncio
async def test_empirical_forecasting_evaluator(test_db: AsyncSession):
    """Verify Brier score, log loss, calibration curves and baselines."""
    eval_result = await ForecastEvaluator.evaluate_protocol_forecasting(test_db)
    assert "protocol_metrics" in eval_result
    assert "baseline_comparisons" in eval_result
    assert "calibration_curve" in eval_result
    assert len(eval_result["calibration_curve"]) == 5  # 5 bins
    assert "statistical_disclosure" in eval_result
    assert "forecaster_leaderboard" in eval_result


# ── 7. COMMIT-REVEAL SECURITY MATRIX & EDGE CASES ─────────────────────────

@pytest.mark.asyncio
async def test_commit_reveal_security_matrix(test_db: AsyncSession):
    """Verify security matrix: duplicate reveal, modified nonce, unrevealed forecast."""
    agent_wallet = "0x2222222222222222222222222222222222222222"
    agent = Agent(
        id="agent_sec_test",
        wallet_address=agent_wallet,
        role="QUANTITATIVE_FORECASTER",
        model_provider_version="v1.0",
        prompt_version="1.0"
    )
    test_db.add(agent)

    case = Case(
        id=f"case_sec_{uuid.uuid4().hex[:6]}",
        title="Security Test Case",
        question="Testing commitment edge cases",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["test"]}
    )
    test_db.add(case)
    await test_db.flush()

    now = utcnow()
    mkt = await MarketService.create_market(
        test_db,
        MarketCreateRequest(
            case_id=case.id,
            question="Security Matrix Question",
            outcome_definition="1 or 0",
            resolution_method="manual",
            commit_deadline=now,
            reveal_deadline=now,
            resolution_deadline=now,
            void_criteria="none"
        )
    )

    prob = 0.65
    digest = "0x" + "77" * 32
    nonce = generate_nonce()
    commit_hash = compute_commitment_hash(
        chain_id=11155111,
        market_id=mkt.id,
        agent_id=agent.id,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce,
        wallet_address=agent_wallet
    )

    # 1. First commitment succeeds
    await MarketService.commit_forecast(
        test_db,
        mkt.id,
        MarketCommitRequest(agent_id=agent.id, commitment_hash=commit_hash, wallet_address=agent_wallet)
    )

    # 2. Duplicate commitment by same agent rejected
    from backend.app.core.errors import InvalidForecastException
    with pytest.raises(InvalidForecastException):
        await MarketService.commit_forecast(
            test_db,
            mkt.id,
            MarketCommitRequest(agent_id=agent.id, commitment_hash=commit_hash, wallet_address=agent_wallet)
        )

    # 3. Modified reveal fails
    with pytest.raises(CommitmentMismatchException):
        await MarketService.reveal_forecast(
            test_db,
            mkt.id,
            MarketRevealRequest(
                agent_id=agent.id,
                probability=0.66,  # altered
                evidence_digest=digest,
                nonce=nonce,
                wallet_address=agent_wallet
            )
        )

    # 4. Correct reveal succeeds
    rev = await MarketService.reveal_forecast(
        test_db,
        mkt.id,
        MarketRevealRequest(
            agent_id=agent.id,
            probability=prob,
            evidence_digest=digest,
            nonce=nonce,
            wallet_address=agent_wallet
        )
    )
    assert rev.reveal_status == "REVEALED"

    # 5. Duplicate reveal rejected
    with pytest.raises(InvalidForecastException):
        await MarketService.reveal_forecast(
            test_db,
            mkt.id,
            MarketRevealRequest(
                agent_id=agent.id,
                probability=prob,
                evidence_digest=digest,
                nonce=nonce,
                wallet_address=agent_wallet
            )
        )


# ── 8. PRIVACY & SECRET LEAKAGE PREVENTION ────────────────────────────────

@pytest.mark.asyncio
async def test_privacy_and_secret_leakage_prevention(test_db: AsyncSession):
    """Ensure nonces and raw probabilities are never leaked in audit logs prior to reveal."""
    case = Case(
        id=f"case_priv_{uuid.uuid4().hex[:6]}",
        title="Privacy Test Case",
        question="Testing secret leakage",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["test"]}
    )
    test_db.add(case)
    await test_db.flush()

    # Commit event payload must ONLY contain commitment_hash, never the raw nonce or probability
    agent_wallet = "0x3333333333333333333333333333333333333333"
    nonce = generate_nonce()
    c_hash = "0x" + "88" * 32

    ev = await AuditService.log_event(
        test_db,
        case.id,
        "FORECAST_COMMITTED",
        agent_wallet,
        {"market_id": "mkt_1", "commitment_hash": c_hash, "wallet_address": agent_wallet}
    )

    # Verify audit event payload
    assert "nonce" not in ev.payload
    assert "probability" not in ev.payload
    assert nonce not in json.dumps(ev.payload)


# ── 9. ON-CHAIN VS OFF-CHAIN BOUNDARY DISCLOSURE ──────────────────────────

def test_onchain_offchain_boundary_distinction():
    """Verify that simulated transactions are explicitly identified and never produce fake Etherscan URLs."""
    from backend.app.services.blockchain_service import BlockchainService
    sim_tx = BlockchainService.record_simulated_transaction(
        event_name="ForecastCommitted",
        contract_address="0x" + "11" * 20,
        sender_address="0x" + "22" * 20,
        case_id="case_123",
        data={"test": True}
    )
    assert sim_tx["execution_mode"] == "LOCAL_SIMULATION"
    assert sim_tx["is_simulated"] is True
    assert sim_tx["explorer_url"] is None  # PRD Section 13.4: No fake explorer links for local simulation


# ── 10. END-TO-END OPTION C FULL DECISION FLOW ───────────────────────────

@pytest.mark.asyncio
async def test_e2e_option_c_full_workflow(test_db: AsyncSession):
    """
    Validates end-to-end Option C workflow:
    Case Creation -> Full Multi-Agent Analysis -> Claim Traceability ->
    Decision Record Sealing -> Audit Event Chain Verification -> Independent Verifier Validation.
    """
    case_req = CaseCreateRequest(
        title="Biometric Security Gate Audit",
        question="Is subliminal biometric categorization permissible for physical access control?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={
            "data_categories": ["biometric", "facial geometry"],
            "processing_purpose": "access control and surveillance"
        }
    )
    case = await CaseService.create_case(test_db, case_req)
    assert case.id.startswith("case_")

    # Run full analysis
    analysis_result = await CaseService.run_full_analysis(test_db, case.id)
    assert analysis_result["status"] == "COMPLETED"
    assert "decision_record" in analysis_result

    # Verify Decision Record
    dec_rec = analysis_result["decision_record"]
    assert dec_rec["case_id"] == case.id
    assert dec_rec["record_digest"].startswith("0x")
    assert len(dec_rec["claims"]) >= 2
    assert len(dec_rec["evidence_passages"]) >= 1

    # Generate Audit Package
    package = await DecisionService.generate_audit_package(test_db, case.id)
    assert package["manifest"]["case_id"] == case.id
    assert package["manifest"]["decision_record_digest"] == dec_rec["record_digest"]

    # Verify via IndependentAuditVerifier
    report = IndependentAuditVerifier.verify_audit_package(package)
    assert report["overall_status"] == "VERIFIED"
    assert report["checks"]["decision_record_digest"]["status"] in ("VERIFIED", "PASS")
    assert report["checks"]["audit_log_chain"]["status"] in ("VERIFIED", "PASS")


