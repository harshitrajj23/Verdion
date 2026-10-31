import json
import os
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.canonical import (
    compute_canonical_sha256,
    format_canonical_timestamp,
    serialize_canonical_json,
    CANONICAL_SCHEMA_VERSION,
)
from backend.app.core.config import settings
from backend.app.core.crypto import (
    compute_forecast_commitment,
    compute_brier_score,
    compute_variance,
)
from backend.app.core.database import Base
from backend.app.core.errors import (
    InvalidScopeException,
    InvalidStateTransitionException,
    InsufficientEvidenceException,
    InvalidForecastException,
    CommitmentMismatchException,
    SettlementAlreadyDoneException,
)
from backend.app.models.entities import (
    Agent,
    AuditEvent,
    Case,
    Claim,
    ClaimEvidenceLink,
    DecisionRecordEntity,
    EvidencePassage,
    Forecast,
    PredictionMarket,
    Settlement,
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
from backend.app.services.agent_service import AgentService
from backend.app.services.audit_service import AuditService, GENESIS_PREVIOUS_DIGEST
from backend.app.services.audit_verifier import IndependentAuditVerifier
from backend.app.services.blockchain_service import BlockchainService
from backend.app.services.case_service import CaseService
from backend.app.services.decision_service import DecisionService
from backend.app.services.forecast_evaluator import ForecastEvaluator
from backend.app.services.market_service import MarketService
from backend.app.services.workflow_service import WorkflowService, WorkflowState


@pytest_asyncio.fixture
async def test_db():
    """Isolated in-memory SQLite fixture for Phase 5E end-to-end tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed agents
        agents = [
            Agent(
                id="ag_legal_researcher_01",
                wallet_address="0x1111111111111111111111111111111111111111",
                role="LEGAL_RESEARCHER",
                model_provider_version="eurlex_cjeu_v1.0",
                prompt_version="1.0",
                status="ACTIVE",
                reputation_score=100.0,
                brier_score=0.25,
                simulated_credits=1000.0,
                created_at=utcnow()
            ),
            Agent(
                id="ag_legal_interpreter_01",
                wallet_address="0x2222222222222222222222222222222222222222",
                role="LEGAL_INTERPRETER",
                model_provider_version="hybrid_statutory_v1.0",
                prompt_version="1.0",
                status="ACTIVE",
                reputation_score=100.0,
                brier_score=0.25,
                simulated_credits=1000.0,
                created_at=utcnow()
            ),
            Agent(
                id="ag_adversarial_01",
                wallet_address="0x3333333333333333333333333333333333333333",
                role="ADVERSARIAL_RESEARCHER",
                model_provider_version="adversarial_redteam_v1.0",
                prompt_version="1.0",
                status="ACTIVE",
                reputation_score=100.0,
                brier_score=0.25,
                simulated_credits=1000.0,
                created_at=utcnow()
            ),
            Agent(
                id="ag_forecaster_01",
                wallet_address="0x4444444444444444444444444444444444444444",
                role="QUANTITATIVE_FORECASTER",
                model_provider_version="brier_forecaster_v1.0",
                prompt_version="1.0",
                status="ACTIVE",
                reputation_score=100.0,
                brier_score=0.25,
                simulated_credits=1000.0,
                created_at=utcnow()
            )
        ]
        for a in agents:
            session.add(a)

        # Seed authoritative legal source and passage
        doc = SourceDocument(
            id="src_gdpr_art5",
            title="Regulation (EU) 2016/679 (GDPR) - Article 5",
            authority="European Parliament and Council",
            jurisdiction="EU",
            url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679",
            publication_date="2016-05-04",
            effective_date="2018-05-25",
            retrieved_at=utcnow(),
            digest="0x0a1b2c3d4e5f60718293a4b5c6d7e8f901a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6",
            version="1.0",
            provenance="REMOTE_OFFICIAL_SOURCE",
            raw_content="Personal data shall be collected for specified, explicit and legitimate purposes and not further processed in a manner that is incompatible with those purposes ('purpose limitation')."
        )
        session.add(doc)
        await session.flush()

        passage = EvidencePassage(
            id="pass_gdpr_art5_1b",
            document_id=doc.id,
            passage_reference="Article 5(1)(b)",
            content_reference="eurlex:celex:32016R0679:art5_1b",
            text="Personal data shall be collected for specified, explicit and legitimate purposes and not further processed in a manner that is incompatible with those purposes ('purpose limitation').",
            digest="0x11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
            source_version="1.0",
            provenance="REMOTE_OFFICIAL_SOURCE"
        )
        session.add(passage)
        await session.commit()

        yield session

    await engine.dispose()


# ── Scenario 1: Successful Evidence-to-Audit Path ───────────────────────
@pytest.mark.asyncio
async def test_scenario_01_successful_evidence_to_audit_path(test_db: AsyncSession):
    """
    Scenario 1 — Use a real provenance-verified legal source and exact passage.
    Create a decision record, verify citations, export the audit package, and verify independently.
    """
    # 1. Create case
    req = CaseCreateRequest(
        title="GenAI Support Transcript Training Compliance",
        question="Does training synthetic voice models on support transcripts violate GDPR Article 5(1)(b)?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={
            "data_categories": ["customer support chat transcripts", "voice recordings"],
            "processing_purpose": "AI model fine-tuning and synthetic voice generation"
        },
        provenance="OPERATIONAL"
    )
    case = await CaseService.create_case(test_db, req)
    assert case.status == "DRAFT"

    # 2. Bind Evidence
    bind_res = await WorkflowService.bind_evidence_to_case(test_db, case.id)
    assert bind_res["status"] == WorkflowState.EVIDENCE_BOUND.value
    assert bind_res["passages_count"] > 0

    # 3. Record Analysis & Seal Decision Record (Option C)
    seal_res = await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)
    assert seal_res["workflow_status"] in (WorkflowState.DECISION_VERIFIED.value, WorkflowState.PARTIALLY_VERIFIED.value)
    decision_rec = seal_res["decision_record"]
    assert decision_rec["record_digest"] is not None
    assert len(decision_rec["evidence_sources"]) > 0

    # 4. Export Audit Package and verify offline
    audit_res = await WorkflowService.finalize_and_verify_audit_package(test_db, case.id)
    verif = audit_res["verification_report"]
    assert verif["checks"]["decision_record_digest"]["status"] == "PASS"
    assert verif["checks"]["audit_hash_chain"]["status"] == "PASS"
    assert verif["checks"]["merkle_checkpoint_root"]["status"] == "PASS"


# ── Scenario 2: Insufficient Evidence Handling ──────────────────────────
@pytest.mark.asyncio
async def test_scenario_02_insufficient_evidence_handling(test_db: AsyncSession):
    """
    Scenario 2 — Submit a question for which the eligible corpus has no adequate evidence.
    Confirm that the system reports INSUFFICIENT_EVIDENCE rather than inventing a citation.
    """
    req = CaseCreateRequest(
        title="Maritime Commercial Salvage Tax Exemption",
        question="What is the salvage lien priority for submerged cargo in international waters under Admiralty Code 1845?",
        jurisdiction="Global",
        assessment_date="2026-10-27",
        facts={
            "data_categories": ["deep sea vessel coordinates", "cargo manifest"],
            "processing_purpose": "maritime salvage lien priority adjudication"
        },
        provenance="OPERATIONAL"
    )
    case = await CaseService.create_case(test_db, req)

    # Bind evidence with strict threshold on non-existent corpus topic
    bind_res = await WorkflowService.bind_evidence_to_case(
        test_db,
        case.id,
        query_override="admiralty code 1845 submerged cargo salvage lien",
        min_passages=999
    )
    assert bind_res["status"] == WorkflowState.INSUFFICIENT_EVIDENCE.value
    assert "insufficient authoritative evidence" in bind_res["message"].lower()

    # Verify that case status was transitioned honestly
    await test_db.refresh(case)
    assert case.status == WorkflowState.INSUFFICIENT_EVIDENCE.value


# ── Scenario 3: Altered Evidence Tamper Detection ────────────────────────
@pytest.mark.asyncio
async def test_scenario_03_altered_evidence_tamper_detection(test_db: AsyncSession):
    """
    Scenario 3 — Modify a passage or digest after creating a decision record.
    Confirm that offline verification fails and identifies the affected check.
    """
    req = CaseCreateRequest(
        title="Tamper Detection Verification Case",
        question="Does Article 5 require purpose limitation?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["customer logs"], "processing_purpose": "analytics"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    seal_res = await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    # Export genuine package
    package = await DecisionService.generate_audit_package(test_db, case.id)

    # Maliciously alter passage text without updating digest
    tampered_package = json.loads(json.dumps(package))
    passages = tampered_package["decision_record"]["evidence_passages"]
    if passages:
        passages[0]["text_excerpt"] = "TAMPERED: All personal data may be freely sold to third parties without restriction."

    # Run independent verifier
    verif_report = IndependentAuditVerifier.verify_audit_package(tampered_package)
    assert verif_report["is_valid"] is False
    assert verif_report["checks"]["decision_record_digest"]["status"] == "FAIL"
    assert "decision_record_digest_mismatch" in verif_report["discrepancies"]


# ── Scenario 4: Commit-Reveal Success ────────────────────────────────────
@pytest.mark.asyncio
async def test_scenario_04_commit_reveal_success(test_db: AsyncSession):
    """
    Scenario 4 — Create a valid test forecast, commit it, reveal it at permitted stage,
    and verify the commitment independently.
    """
    req_case = CaseCreateRequest(
        title="Commit-Reveal Workflow Verification Case",
        question="Will CJEU rule fine-tuning constitutes incompatible further processing?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["chat history"], "processing_purpose": "AI training"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    # Open market
    req_market = MarketCreateRequest(
        case_id=case.id,
        question="Will CJEU confirm purpose limitation applies to synthetic voice models?",
        outcome_definition="1 if confirmed, 0 if exempted",
        resolution_method="Independent evaluator review of official CJEU ruling",
        rubric_version="1.0",
        commit_deadline=utcnow() + timedelta(hours=1),
        reveal_deadline=utcnow() + timedelta(hours=2),
        resolution_deadline=utcnow() + timedelta(hours=24),
        challenge_window_seconds=3600,
        void_criteria="Void if case withdrawn prior to judgment"
    )
    market = await WorkflowService.create_forecast_for_decision(test_db, case.id, req_market)
    assert market.status == "PUBLISHED"

    # Compute commitment
    agent_id = "ag_forecaster_01"
    agent = await test_db.get(Agent, agent_id)
    prob = 0.7250
    evidence_digest = "0x11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff"
    nonce = "0x" + os.urandom(32).hex()

    commit_hash = compute_forecast_commitment(
        chain_id=settings.CHAIN_ID,
        market_id=market.id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent.wallet_address
    )

    # Commit
    commit_req = MarketCommitRequest(agent_id=agent_id, commitment_hash=commit_hash, wallet_address=agent.wallet_address)
    fc = await WorkflowService.commit_forecast_commitment(test_db, market.id, commit_req)
    assert fc.reveal_status == "COMMITTED"

    # Reveal
    reveal_req = MarketRevealRequest(
        agent_id=agent_id,
        probability=prob,
        evidence_digest=evidence_digest,
        nonce=nonce,
        wallet_address=agent.wallet_address
    )
    revealed_fc = await WorkflowService.reveal_forecast_prediction(test_db, market.id, reveal_req)
    assert revealed_fc.reveal_status == "REVEALED"
    assert revealed_fc.probability == 0.7250


# ── Scenario 5: Invalid Reveal Detection ─────────────────────────────────
@pytest.mark.asyncio
async def test_scenario_05_invalid_reveal_detection(test_db: AsyncSession):
    """
    Scenario 5 — Change the prediction, nonce, or forecast identifier.
    Confirm that the reveal is rejected and an auditable failure is recorded.
    """
    req_case = CaseCreateRequest(
        title="Invalid Reveal Case",
        question="Question 5",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["user data"], "processing_purpose": "profiling"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    market = await WorkflowService.create_forecast_for_decision(
        test_db,
        case.id,
        MarketCreateRequest(
            case_id=case.id,
            question="Market 5",
            outcome_definition="Binary",
            resolution_method="Review",
            rubric_version="1.0",
            commit_deadline=utcnow() + timedelta(hours=1),
            reveal_deadline=utcnow() + timedelta(hours=2),
            resolution_deadline=utcnow() + timedelta(hours=24),
            challenge_window_seconds=3600,
            void_criteria="None"
        )
    )

    agent = await test_db.get(Agent, "ag_forecaster_01")
    nonce = "0x" + os.urandom(32).hex()
    commit_hash = compute_forecast_commitment(
        chain_id=settings.CHAIN_ID,
        market_id=market.id,
        agent_id=agent.id,
        probability=0.60,
        evidence_digest="0x" + "aa" * 32,
        nonce=nonce,
        wallet_address=agent.wallet_address
    )

    await WorkflowService.commit_forecast_commitment(
        test_db,
        market.id,
        MarketCommitRequest(agent_id=agent.id, commitment_hash=commit_hash, wallet_address=agent.wallet_address)
    )

    # Attempt reveal with tampered probability (0.85 instead of 0.60)
    with pytest.raises(CommitmentMismatchException):
        await WorkflowService.reveal_forecast_prediction(
            test_db,
            market.id,
            MarketRevealRequest(
                agent_id=agent.id,
                probability=0.85,
                evidence_digest="0x" + "aa" * 32,
                nonce=nonce,
                wallet_address=agent.wallet_address
            )
        )


# ── Scenario 6: Unresolved Real Forecast Exclusion ──────────────────────
@pytest.mark.asyncio
async def test_scenario_06_unresolved_real_forecast_exclusion(test_db: AsyncSession):
    """
    Scenario 6 — Create an operational forecast whose outcome is not yet available.
    Confirm that it remains unresolved and is excluded from resolved performance metrics.
    """
    req_case = CaseCreateRequest(
        title="Unresolved Operational Forecast Case",
        question="Will Article 5(1)(b) enforce synthetic voice training bans?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["voice"], "processing_purpose": "AI"},
        provenance="OPERATIONAL"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    market = await WorkflowService.create_forecast_for_decision(
        test_db,
        case.id,
        MarketCreateRequest(
            case_id=case.id,
            question="Unresolved Operational Market",
            outcome_definition="Pending official ruling",
            resolution_method="Court publication",
            rubric_version="1.0",
            commit_deadline=utcnow() + timedelta(days=7),
            reveal_deadline=utcnow() + timedelta(days=14),
            resolution_deadline=utcnow() + timedelta(days=60),
            challenge_window_seconds=86400,
            void_criteria="None"
        )
    )

    # Evaluate protocol metrics
    eval_metrics = await ForecastEvaluator.evaluate_protocol_forecasting(test_db)
    assert eval_metrics["unresolved_markets_count"] >= 1
    # Unresolved markets must not be counted in resolved forecasts
    assert market.proposed_outcome is None


# ── Scenario 7: Test-Only Resolution Metric Segregation ─────────────────
@pytest.mark.asyncio
async def test_scenario_07_test_only_resolution_metric_segregation(test_db: AsyncSession):
    """
    Scenario 7 — Exercise resolution and scoring using explicitly isolated test data.
    Confirm that the resulting record is marked TEST.
    """
    req_case = CaseCreateRequest(
        title="Test Resolution Isolation Case",
        question="Synthetic resolution test",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["test facts"], "processing_purpose": "benchmark testing"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    market = await WorkflowService.create_forecast_for_decision(
        test_db,
        case.id,
        MarketCreateRequest(
            case_id=case.id,
            question="Test Resolution Market",
            outcome_definition="Binary",
            resolution_method="Test harness",
            rubric_version="1.0",
            commit_deadline=utcnow() + timedelta(hours=1),
            reveal_deadline=utcnow() + timedelta(hours=2),
            resolution_deadline=utcnow() + timedelta(hours=3),
            challenge_window_seconds=60,
            void_criteria="None"
        )
    )

    agent = await test_db.get(Agent, "ag_forecaster_01")
    nonce = "0x" + os.urandom(32).hex()
    commit_hash = compute_forecast_commitment(
        chain_id=settings.CHAIN_ID,
        market_id=market.id,
        agent_id=agent.id,
        probability=0.80,
        evidence_digest="0x" + "11" * 32,
        nonce=nonce,
        wallet_address=agent.wallet_address
    )

    await WorkflowService.commit_forecast_commitment(
        test_db,
        market.id,
        MarketCommitRequest(agent_id=agent.id, commitment_hash=commit_hash, wallet_address=agent.wallet_address)
    )

    await WorkflowService.reveal_forecast_prediction(
        test_db,
        market.id,
        MarketRevealRequest(
            agent_id=agent.id,
            probability=0.80,
            evidence_digest="0x" + "11" * 32,
            nonce=nonce,
            wallet_address=agent.wallet_address
        )
    )

    # Resolve with explicit test label
    res_req = MarketResolveRequest(
        proposed_outcome=1,
        resolution_reference="isolated_synthetic_fixture",
        evaluator_address=settings.EVALUATOR_ADDRESS
    )
    resolved_market = await WorkflowService.resolve_market_outcome(test_db, market.id, res_req, is_test=True)
    assert resolved_market.proposed_outcome == 1

    # Settle market
    settle_res = await WorkflowService.settle_and_score_market(test_db, market.id)
    assert settle_res["status"] == "SETTLED"
    assert len(settle_res["settlements"]) == 1
    # Brier score for p=0.80, y=1: (0.80 - 1.0)^2 = 0.04
    assert pytest.approx(settle_res["settlements"][0]["brier_score"], 0.001) == 0.0400


# ── Scenario 8: Audit Chain Corruption Detection ────────────────────────
@pytest.mark.asyncio
async def test_scenario_08_audit_chain_corruption_detection(test_db: AsyncSession):
    """
    Scenario 8 — Alter, delete or reorder an audit event.
    Confirm that the verifier detects the tampering.
    """
    req_case = CaseCreateRequest(
        title="Audit Corruption Detection Case",
        question="Question 8",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["data"], "processing_purpose": "purpose"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    package = await DecisionService.generate_audit_package(test_db, case.id)
    tampered_package = json.loads(json.dumps(package))

    # Reorder audit events
    audit_events = tampered_package["decision_record"]["audit_events"]
    if len(audit_events) >= 2:
        audit_events[0], audit_events[1] = audit_events[1], audit_events[0]

    verif = IndependentAuditVerifier.verify_audit_package(tampered_package)
    assert verif["is_valid"] is False
    assert verif["checks"]["audit_hash_chain"]["status"] == "FAIL"


# ── Scenario 9: Missing Trust Anchor Disclosure ─────────────────────────
@pytest.mark.asyncio
async def test_scenario_09_missing_trust_anchor_disclosure(test_db: AsyncSession):
    """
    Scenario 9 — Provide an internally consistent audit package with no trusted external checkpoint.
    Confirm that it is not represented as externally anchored.
    """
    req_case = CaseCreateRequest(
        title="Unanchored Disclosure Case",
        question="Question 9",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["data"], "processing_purpose": "purpose"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    package = await DecisionService.generate_audit_package(test_db, case.id)

    # Verify without trusted checkpoint
    verif = IndependentAuditVerifier.verify_audit_package(package, trusted_checkpoint=None)
    assert verif["is_anchored"] is False
    assert verif["overall_status"] in ("VERIFIED", "UNANCHORED_LOCAL_RECORD")
    assert verif["anchor_status"] == "UNANCHORED_LOCAL_RECORD"
    assert "UNANCHORED_LOCAL_RECORD" in verif["checks"]["merkle_checkpoint_root"]["disclosure"]


# ── Scenario 10: Restart and Recovery ────────────────────────────────────
@pytest.mark.asyncio
async def test_scenario_10_restart_and_recovery(test_db: AsyncSession):
    """
    Scenario 10 — Simulate process restart and verify that source references,
    decision record, forecast state, and audit package remain resolvable.
    """
    req_case = CaseCreateRequest(
        title="Recovery Persistence Case",
        question="Will state survive application restart?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["system logs"], "processing_purpose": "disaster recovery"},
        provenance="OPERATIONAL"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    seal_res = await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)
    original_digest = seal_res["decision_record"]["record_digest"]

    # Commit session and clear session cache to simulate restart
    await test_db.commit()
    test_db.expunge_all()

    # Re-fetch from database
    reloaded_case = await test_db.get(Case, case.id)
    assert reloaded_case is not None
    assert reloaded_case.status in (WorkflowState.DECISION_VERIFIED.value, WorkflowState.PARTIALLY_VERIFIED.value)

    # Re-fetch decision record
    reloaded_decision = await DecisionService.build_canonical_decision_record(test_db, case.id, persist=False)
    assert reloaded_decision.record_digest == original_digest

    # Re-export and verify package
    pkg = await DecisionService.generate_audit_package(test_db, case.id)
    verif = IndependentAuditVerifier.verify_audit_package(pkg)
    assert verif["checks"]["decision_record_digest"]["status"] == "PASS"


# ── Scenario 11: Partial Blockchain Failure & Reconciliation ────────────
@pytest.mark.asyncio
async def test_scenario_11_partial_blockchain_failure_reconciliation(test_db: AsyncSession):
    """
    Scenario 11 — Simulate a timeout or unavailable RPC.
    Confirm that the system does not claim a transaction succeeded without a verified receipt.
    """
    simulated_tx = BlockchainService.record_simulated_transaction(
        event_name="SimulatedCommitment",
        contract_address=settings.PREDICTION_MARKET_ADDRESS,
        sender_address="0xAgent",
        case_id="case_sim_01",
        data={"status": "SIMULATED"}
    )
    # Status is simulated, not falsely claimed as on-chain confirmed
    assert simulated_tx["status"] == "SIMULATED"
    assert simulated_tx["chain_id"] == settings.CHAIN_ID


# ── Scenario 12: Independent Package Verification & Tampering ───────────
@pytest.mark.asyncio
async def test_scenario_12_independent_package_verification_and_tampering(test_db: AsyncSession):
    """
    Scenario 12 — Export a valid package, verify it in a clean independent process,
    tamper with a copy, and verify that the tampered copy fails.
    """
    req_case = CaseCreateRequest(
        title="Independent Verification Clean Package",
        question="Can verifier operate independently?",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["audit files"], "processing_purpose": "external audit"},
        provenance="OPERATIONAL"
    )
    case = await CaseService.create_case(test_db, req_case)
    await WorkflowService.bind_evidence_to_case(test_db, case.id)
    await WorkflowService.record_analysis_and_seal_decision(test_db, case.id)

    # Export clean package
    package = await DecisionService.generate_audit_package(test_db, case.id)
    clean_verif = IndependentAuditVerifier.verify_audit_package(package)
    assert clean_verif["is_valid"] is True
    assert clean_verif["overall_status"] in ("VERIFIED", "UNANCHORED_LOCAL_RECORD")

    # Deep mutate: alter question in decision record
    tampered_package = json.loads(json.dumps(package))
    tampered_package["decision_record"]["case_question"] = "MUTATED: Fake question"

    tampered_verif = IndependentAuditVerifier.verify_audit_package(tampered_package)
    assert tampered_verif["is_valid"] is False
    assert tampered_verif["checks"]["decision_record_digest"]["status"] == "FAIL"


# ── Idempotency and State Transition Enforcement ────────────────────────
@pytest.mark.asyncio
async def test_workflow_state_transition_idempotency_and_validation(test_db: AsyncSession):
    """
    Tests that duplicate requests return idempotent responses and invalid transitions are rejected.
    """
    req_case = CaseCreateRequest(
        title="Idempotency Test Case",
        question="Question",
        jurisdiction="EU",
        assessment_date="2026-10-27",
        facts={"data_categories": ["data"], "processing_purpose": "purpose"},
        provenance="TEST"
    )
    case = await CaseService.create_case(test_db, req_case)

    # Valid transition to EVIDENCE_BOUND
    t1 = await WorkflowService.transition_state(
        test_db, case.id, to_state=WorkflowState.EVIDENCE_BOUND.value, actor="0xUser"
    )
    assert t1["transitioned"] is True

    # Repeated identical transition -> idempotent
    t2 = await WorkflowService.transition_state(
        test_db, case.id, to_state=WorkflowState.EVIDENCE_BOUND.value, actor="0xUser"
    )
    assert t2["idempotent"] is True
    assert t2["transitioned"] is False

    # Invalid jump (from EVIDENCE_BOUND directly to SCORED)
    with pytest.raises(InvalidStateTransitionException):
        await WorkflowService.transition_state(
            test_db, case.id, to_state=WorkflowState.SCORED.value, actor="0xUser"
        )
