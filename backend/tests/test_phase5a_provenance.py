import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.database import Base
from backend.app.schemas.case import CaseCreateRequest
from backend.app.services.case_service import CaseService


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_case_provenance_assignment_and_filtering(test_db):
    """Verify cases are tagged with explicit provenance and filtered appropriately."""
    # 1. Create an OPERATIONAL case
    c1 = await CaseService.create_case(
        test_db,
        CaseCreateRequest(
            title="Real Operational Case",
            question="Is data processing compliant?",
            jurisdiction="EU",
            assessment_date="2026-10-19",
            facts={"processing_purpose": "analytics", "data_categories": ["email"]},
            provenance="OPERATIONAL"
        )
    )
    assert c1.provenance == "OPERATIONAL"

    # 2. Create a DEMO case
    c2 = await CaseService.create_case(
        test_db,
        CaseCreateRequest(
            title="Demo Customer Case",
            question="Is demo processing compliant?",
            jurisdiction="EU",
            assessment_date="2026-10-19",
            facts={"processing_purpose": "demo", "data_categories": ["audio"]},
            provenance="DEMO"
        )
    )
    assert c2.provenance == "DEMO"

    # 3. Create a TEST case
    c3 = await CaseService.create_case(
        test_db,
        CaseCreateRequest(
            title="Test Case",
            question="Is test processing compliant?",
            jurisdiction="EU",
            assessment_date="2026-10-19",
            facts={"processing_purpose": "test", "data_categories": ["logs"]},
            provenance="TEST"
        )
    )
    assert c3.provenance == "TEST"

    # 4. Filter: exclude_test=True (Default) -> Should return OPERATIONAL and DEMO (2 cases)
    filtered = await CaseService.get_all_cases(test_db, exclude_test=True)
    assert len(filtered) == 2
    assert all(c.provenance != "TEST" for c in filtered)

    # 5. Filter: provenance='OPERATIONAL' -> Should return 1 case
    op_only = await CaseService.get_all_cases(test_db, provenance="OPERATIONAL")
    assert len(op_only) == 1
    assert op_only[0].id == c1.id

    # 6. Filter: provenance='DEMO' -> Should return 1 case
    demo_only = await CaseService.get_all_cases(test_db, provenance="DEMO")
    assert len(demo_only) == 1
    assert demo_only[0].id == c2.id
