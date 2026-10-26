from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.config import settings
from backend.app.core.crypto import compute_commitment_hash, generate_nonce
from backend.app.core.database import Base
from backend.app.models.entities import Agent
from backend.app.core.errors import (
    CommitmentMismatchException,
    InvalidScopeException,
    SettlementAlreadyDoneException,
    UnauthorizedResolutionException,
)
from backend.app.schemas.bounty import (
    BountyChallengeRequest,
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
from backend.app.services.retrieval_service import RetrievalService


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


@pytest.mark.asyncio
async def test_prediction_market_commit_reveal_and_settle(test_db):
    now = datetime.now(timezone.utc)
    case_req = CaseCreateRequest(
        title="Market Case",
        question="Question",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={"data_categories": ["audio"], "processing_purpose": "training"}
    )
    case = await CaseService.create_case(test_db, case_req)

    # 1. Create Market
    m_req = MarketCreateRequest(
        case_id=case.id,
        question="Will compliance gap be confirmed?",
        outcome_definition="1 if gap exists, 0 otherwise",
        resolution_method="Independent evaluator audit",
        commit_deadline=now + timedelta(hours=1),
        reveal_deadline=now + timedelta(hours=2),
        resolution_deadline=now + timedelta(hours=3),
        challenge_window_seconds=86400,
        void_criteria="Void if statute repealed",
        evaluator_address=settings.EVALUATOR_ADDRESS
    )
    market = await MarketService.create_market(test_db, m_req)
    assert market.id.startswith("mkt_")

    # 2. Commit Forecast
    agent_id = "agent_legal_researcher"
    agent = await test_db.get(Agent, agent_id)
    assert agent is not None and agent.wallet_address.startswith("0x")
    prob = 0.85
    digest = "0x" + "a" * 64
    nonce = generate_nonce()

    c_hash = compute_commitment_hash(
        chain_id=settings.CHAIN_ID,
        market_id=market.id,
        agent_id=agent_id,
        probability=prob,
        evidence_digest=digest,
        nonce=nonce,
        wallet_address=agent.wallet_address
    )

    commit_res = await MarketService.commit_forecast(
        test_db,
        market.id,
        MarketCommitRequest(agent_id=agent_id, commitment_hash=c_hash, wallet_address=agent.wallet_address)
    )
    assert commit_res.reveal_status == "COMMITTED"

    # 3. Reveal with invalid nonce fails
    with pytest.raises(CommitmentMismatchException):
        await MarketService.reveal_forecast(
            test_db,
            market.id,
            MarketRevealRequest(
                agent_id=agent_id,
                probability=prob,
                evidence_digest=digest,
                nonce=generate_nonce(),  # Wrong nonce!
                wallet_address=agent.wallet_address
            )
        )

    # 4. Reveal with valid nonce succeeds
    reveal_res = await MarketService.reveal_forecast(
        test_db,
        market.id,
        MarketRevealRequest(
            agent_id=agent_id,
            probability=prob,
            evidence_digest=digest,
            nonce=nonce,
            wallet_address=agent.wallet_address
        )
    )
    assert reveal_res.reveal_status == "REVEALED"
    assert reveal_res.probability == 0.85

    # 5. Unauthorized resolution fails
    with pytest.raises(UnauthorizedResolutionException):
        await MarketService.propose_resolution(
            test_db,
            market.id,
            MarketResolveRequest(
                proposed_outcome=1,
                resolution_reference="Audit #1",
                evaluator_address="0xUnauthorizedHacker"
            )
        )

    # 6. Authorized resolution succeeds
    await MarketService.propose_resolution(
        test_db,
        market.id,
        MarketResolveRequest(
            proposed_outcome=1,
            resolution_reference="Audit #1",
            evaluator_address=settings.EVALUATOR_ADDRESS
        )
    )

    # 7. Settlement succeeds & scores with Brier score
    settle_res = await MarketService.settle_market(test_db, market.id, settler_address=settings.EVALUATOR_ADDRESS)
    assert settle_res["status"] == "SETTLED"
    assert len(settle_res["settlements"]) == 1
    # Brier score: (0.85 - 1)^2 = 0.0225
    assert round(settle_res["settlements"][0]["brier_score"], 4) == 0.0225
    assert settle_res["settlements"][0]["tx_hash"] is None
    assert settle_res["settlements"][0]["status"] == "pending"

    # 8. Duplicate settlement fails (FR-052)
    with pytest.raises(SettlementAlreadyDoneException):
        await MarketService.settle_market(test_db, market.id, settler_address=settings.EVALUATOR_ADDRESS)


@pytest.mark.asyncio
async def test_bounty_submission_duplicate_check_and_settle(test_db):
    now = datetime.now(timezone.utc)
    case_req = CaseCreateRequest(
        title="Bounty Case",
        question="Question",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={"data_categories": ["text"], "processing_purpose": "test"}
    )
    case = await CaseService.create_case(test_db, case_req)

    # 1. Create Bounty
    b_req = BountyCreateRequest(
        case_id=case.id,
        question="Find EDPB ruling on secondary training",
        acceptance_criteria="Official EDPB reference",
        reward_amount=100.0,
        deadline=now + timedelta(days=2),
        challenge_window_seconds=86400
    )
    bounty = await BountyService.create_bounty(test_db, b_req)
    assert bounty.id.startswith("bnty_")

    # 2. Submit Evidence
    sub_req = EvidenceSubmissionRequest(
        contributor_address="0xContributor1",
        title="EDPB Guideline",
        source_reference="EDPB 3/2019",
        content="Secondary processing requires independent lawful basis.",
        provenance={"source": "EU Gazette"}
    )
    sub = await BountyService.submit_evidence(test_db, bounty.id, sub_req)
    assert sub.id.startswith("sub_")

    # 3. Duplicate submission rejected (FR-045)
    with pytest.raises(InvalidScopeException):
        await BountyService.submit_evidence(test_db, bounty.id, sub_req)

    # 4. Challenge submission
    chall = await BountyService.challenge_submission(
        test_db,
        sub.id,
        BountyChallengeRequest(
            challenger_address="0xChallenger",
            reason="Guideline might have been updated by 2024 draft"
        )
    )
    assert chall.status == "CHALLENGED"

    # 5. Settle Bounty
    settle_res = await BountyService.settle_bounty(
        test_db,
        bounty.id,
        BountySettleRequest(
            winning_submission_id=sub.id,
            reviewer_address=settings.EVALUATOR_ADDRESS,
            review_reason="Authority confirmed and verified."
        )
    )
    assert settle_res["status"] == "SETTLED"
    assert settle_res["reward_amount"] == 100.0

    # 6. Duplicate settlement fails (FR-052)
    with pytest.raises(SettlementAlreadyDoneException):
        await BountyService.settle_bounty(
            test_db,
            bounty.id,
            BountySettleRequest(
                winning_submission_id=sub.id,
                reviewer_address=settings.EVALUATOR_ADDRESS,
                review_reason="Duplicate attempt."
            )
        )
