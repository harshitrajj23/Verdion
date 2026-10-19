import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.database import Base
from backend.app.core.errors import InvalidScopeException
from backend.app.schemas.case import CaseCreateRequest, CaseUpdateRequest
from backend.app.services.agent_service import AgentService
from backend.app.services.case_service import CaseService
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
async def test_case_creation_and_scope_validation(test_db):
    # Valid case creation
    req = CaseCreateRequest(
        title="AI Training Risk Assessment",
        question="Assess compliance of training AI on support audio",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={
            "data_categories": ["voice recordings"],
            "processing_purpose": "AI training"
        }
    )
    case = await CaseService.create_case(test_db, req)
    assert case.id.startswith("case_")
    assert case.scope_version == 1
    assert case.status == "DRAFT"

    # Missing material facts fails
    invalid_req = CaseCreateRequest(
        title="Invalid Case",
        question="Invalid Question",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={}  # Missing required fields
    )
    with pytest.raises(InvalidScopeException):
        await CaseService.create_case(test_db, invalid_req)


@pytest.mark.asyncio
async def test_case_scope_versioning(test_db):
    req = CaseCreateRequest(
        title="Initial Version",
        question="Initial Question",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={"data_categories": ["names"], "processing_purpose": "billing"}
    )
    case = await CaseService.create_case(test_db, req)
    assert case.scope_version == 1

    # Material update increments version
    update_req = CaseUpdateRequest(
        title="Updated Title Scope"
    )
    updated = await CaseService.update_case(test_db, case.id, update_req)
    assert updated.scope_version == 2
    assert updated.title == "Updated Title Scope"


@pytest.mark.asyncio
async def test_retrieval_and_multi_agent_workflow(test_db):
    req = CaseCreateRequest(
        title="Support Transcript Analysis",
        question="Assess GDPR compliance of conversational AI training",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={
            "data_categories": ["chat transcripts"],
            "processing_purpose": "secondary: model improvement",
            "user_notice_provided": False,
            "retention_policy": "indefinite",
            "deletion_mechanism": "none",
            "secondary_ai_training": True
        }
    )
    case = await CaseService.create_case(test_db, req)

    # Run full analysis
    analysis = await CaseService.run_full_analysis(test_db, case.id)

    assert analysis["case_id"] == case.id
    assert analysis["status"] == "COMPLETED"
    assert len(analysis["agent_outputs"]) >= 4

    # Verify argument graph has claims and edges
    graph = analysis["argument_graph"]
    assert len(graph["claims"]) > 0
    assert len(graph["edges"]) > 0
    assert any(e["relationship_type"] == "CONTRADICTS" for e in graph["edges"])
