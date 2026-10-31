from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.crypto import compute_commitment_hash, generate_nonce
from backend.app.core.database import get_db, init_db
from backend.app.models.entities import Agent
from backend.app.schemas.bounty import (

    BountyCreateRequest,
    BountySettleRequest,
    EvidenceSubmissionRequest,
)
from backend.app.schemas.case import CaseCreateRequest
from backend.app.schemas.market import (
    MarketCommitRequest,
    MarketCreateRequest,
    MarketResolveRequest,
    MarketRevealRequest,
)
from backend.app.services.agent_service import AgentService
from backend.app.services.bounty_service import BountyService
from backend.app.services.case_service import CaseService
from backend.app.services.market_service import MarketService
from backend.app.services.reporting_service import ReportingService
from backend.app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/demo", tags=["Demo & Simulation"])


@router.post("/seed")
async def seed_demo_workflow(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Executes the complete Appendix A end-to-end benchmark workflow:
    1. Initializes legal corpus & default agents.
    2. Creates Case (A.1 AI-enabled customer analytics).
    3. Runs multi-agent investigation & hybrid verification (A.2).
    4. Creates Prediction Market & commits/reveals forecasts with cryptographic hashes (A.3).
    5. Opens Evidence Bounty, submits verified authority, and settles simulated credits (A.4).
    6. Resolves and settles Prediction Market with Brier scoring.
    7. Generates comprehensive 10-section final report.
    """
    # 0. Ensure tables exist
    await init_db()
    # 1. Init corpus and agents
    await RetrievalService.initialize_corpus(db)
    await AgentService.initialize_agents(db)

    # 2. Create Case (Appendix A.1)
    case_req = CaseCreateRequest(
        title="AI-Powered Customer Support Analytics",
        question="Assess compliance risks of processing customer-support conversations to train an AI foundation model",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={
            "data_categories": ["customer support chat transcripts", "voice recordings", "account emails"],
            "processing_purpose": "original: technical support resolution; secondary: LLM training",
            "user_notice_provided": False,
            "user_consent_obtained": False,
            "retention_policy": "indefinite",
            "deletion_mechanism": "manual refusal",
            "secondary_ai_training": True,
            "human_in_the_loop": False,
            "solely_automated_decision": True
        },
        provenance="DEMO"
    )
    case = await CaseService.create_case(db, case_req, creator_address="0xComplianceLead")

    # 3. Run multi-agent investigation (Appendix A.2)
    analysis_result = await CaseService.run_full_analysis(db, case.id)

    # 4. Create Prediction Market (Appendix A.3)
    now = datetime.now(timezone.utc)
    market_req = MarketCreateRequest(
        case_id=case.id,
        question="Will the independent evaluator identify at least one material, unresolved compliance gap under the frozen facts and rubric?",
        outcome_definition="1 (YES) if independent legal audit verifies statutory violation under GDPR Art 5(1)(b) or Art 13; 0 (NO) otherwise.",
        resolution_method="Independent evaluator reviews deterministic checks and passage citations against published rubric v1.0",
        rubric_version="1.0",
        commit_deadline=now + timedelta(hours=2),
        reveal_deadline=now + timedelta(hours=4),
        resolution_deadline=now + timedelta(hours=24),
        challenge_window_seconds=86400,
        void_criteria="Void if regulatory framework is repealed before resolution deadline.",
        evaluator_address=settings.EVALUATOR_ADDRESS
    )
    market = await MarketService.create_market(db, market_req, creator_address="0xComplianceLead")

    # Simulate 3 Agent Forecasts (Appendix A.3: e.g. 0.80, 0.65, 0.45)
    forecast_data = [
        {"agent_id": "agent_legal_researcher", "prob": 0.80, "digest": "0x" + "a" * 64, "nonce": generate_nonce()},
        {"agent_id": "agent_legal_interpreter", "prob": 0.65, "digest": "0x" + "b" * 64, "nonce": generate_nonce()},
        {"agent_id": "agent_adversarial_researcher", "prob": 0.45, "digest": "0x" + "c" * 64, "nonce": generate_nonce()},
    ]

    # Commit phase
    for fd in forecast_data:
        agent = await db.get(Agent, fd["agent_id"])
        agent_wallet = agent.wallet_address if agent else None
        c_hash = compute_commitment_hash(
            chain_id=settings.CHAIN_ID,
            market_id=market.id,
            agent_id=fd["agent_id"],
            probability=fd["prob"],
            evidence_digest=fd["digest"],
            nonce=fd["nonce"],
            wallet_address=agent_wallet
        )
        fd["commitment_hash"] = c_hash
        await MarketService.commit_forecast(
            db=db,
            market_id=market.id,
            req=MarketCommitRequest(agent_id=fd["agent_id"], commitment_hash=c_hash, wallet_address=agent_wallet),
            sender_address=agent_wallet or "0xAgent"
        )

    # Reveal phase
    for fd in forecast_data:
        agent = await db.get(Agent, fd["agent_id"])
        agent_wallet = agent.wallet_address if agent else None
        await MarketService.reveal_forecast(
            db=db,
            market_id=market.id,
            req=MarketRevealRequest(
                agent_id=fd["agent_id"],
                probability=fd["prob"],
                evidence_digest=fd["digest"],
                nonce=fd["nonce"],
                wallet_address=agent_wallet
            ),
            sender_address=agent_wallet or "0xAgent"
        )

    # 5. Evidence Bounty (Appendix A.4)
    bounty_req = BountyCreateRequest(
        case_id=case.id,
        question="Provide authoritative regulatory guidance on whether customer support chat transcripts qualify for legitimate interest AI training under GDPR Art 6(1)(f)",
        acceptance_criteria="Authoritative citation from EDPB Guidelines or CJEU jurisprudence establishing legitimate interest criteria for AI model pre-training",
        reward_amount=100.0,
        deadline=now + timedelta(days=3),
        challenge_window_seconds=86400,
        creator_address="0xCoordinator"
    )
    bounty = await BountyService.create_bounty(db, bounty_req, creator_address="0xCoordinator")

    # Contributor submits evidence
    sub_req = EvidenceSubmissionRequest(
        contributor_address="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        title="EDPB Guidelines 3/2019 on Processing of Personal Data through Video and Voice Devices",
        source_reference="EDPB Guidelines 3/2019 paragraph 44",
        content="Secondary processing of customer interactions for AI algorithmic training requires a separate compatibility test under Art 6(4) unless specific consent was provided at collection.",
        provenance={"retrieval_method": "official_gazette_crawl", "verified": True}
    )
    sub = await BountyService.submit_evidence(db, bounty.id, sub_req)

    # Settle bounty
    bounty_settle_res = await BountyService.settle_bounty(
        db=db,
        bounty_id=bounty.id,
        req=BountySettleRequest(
            winning_submission_id=sub.id,
            reviewer_address=settings.EVALUATOR_ADDRESS,
            review_reason="Satisfies EDPB citation rubric and directly answers secondary processing uncertainty."
        )
    )

    # 6. Resolve and settle Prediction Market
    await MarketService.propose_resolution(
        db=db,
        market_id=market.id,
        req=MarketResolveRequest(
            proposed_outcome=1,  # 1 = Gap Confirmed
            resolution_reference="Audit verdict: Independent evaluation verified Purpose Limitation violation under GDPR Art 5(1)(b)",
            evaluator_address=settings.EVALUATOR_ADDRESS
        )
    )
    market_settle_res = await MarketService.settle_market(db, market.id, settler_address=settings.EVALUATOR_ADDRESS)

    # 7. Generate Final Report
    report = await ReportingService.generate_final_report(db, case.id)

    return {
        "status": "DEMO_SEEDED_SUCCESSFULLY",
        "case_id": case.id,
        "market_id": market.id,
        "bounty_id": bounty.id,
        "market_settlement": market_settle_res,
        "bounty_settlement": bounty_settle_res,
        "final_report": report
    }
