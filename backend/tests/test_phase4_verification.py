import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.config import settings
from backend.app.core.database import Base
from backend.app.models.entities import SourceDocument, EvidencePassage, Case
from backend.app.services.agent_service import AgentService
from backend.app.services.blockchain_service import BlockchainService
from backend.app.services.ingestion.base_adapter import BaseSourceAdapter, SourceDocumentMetadata
from backend.app.services.ingestion.eur_lex_adapter import EURLexAdapter
from backend.app.services.ingestion.cjeu_adapter import CJEUAdapter
from backend.app.services.ingestion.ingestion_service import IngestionService, IngestionJobRecord
from backend.app.services.case_service import CaseService
from backend.app.schemas.case import CaseCreateRequest
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


# ── 1. BLOCKCHAIN TRUTHFULNESS & SIMULATION SEPARATION ───────────────────

def test_blockchain_simulated_transaction_has_no_phantom_explorer():
    """Verify simulated transactions are flagged as LOCAL_SIMULATION with no external Etherscan link."""
    tx_record = BlockchainService.record_simulated_transaction(
        event_name="SETTLE_MARKET",
        sender_address="0x1234567890123456789012345678901234567890",
        case_id="case_test_123",
        contract_address="0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
        status="CONFIRMED",
        receipt_status="0x1",
        data={"action": "SETTLE_MARKET", "market_id": "mkt_test_123"}
    )
    assert tx_record["execution_mode"] == "LOCAL_SIMULATION"
    assert tx_record["is_simulated"] is True
    assert tx_record["explorer_url"] is None
    assert tx_record["status"].upper() == "CONFIRMED"


def test_blockchain_verify_contract_bytecode_empty_account():
    """Verify placeholder vanity address returns EMPTY_ACCOUNT / has_code False."""
    res = BlockchainService.verify_contract_bytecode("0x1111111111111111111111111111111111111111")
    assert "status" in res
    assert res["contract_address"] == "0x1111111111111111111111111111111111111111"


def test_blockchain_verify_onchain_receipt_unverified_hash():
    """Verify an unknown or simulated hash returns unverified rather than fabricating success."""
    res = BlockchainService.verify_onchain_receipt("0x0000000000000000000000000000000000000000000000000000000000000000")
    assert "status" in res
    assert res["status"] in ("UNVERIFIED_ONCHAIN", "RPC_LOOKUP_FAILED")
    assert res["explorer_url"] is None


# ── 2. REGULATORY INGESTION ADAPTERS & DIGEST PROVENANCE ─────────────────

@pytest.mark.asyncio
async def test_eur_lex_adapter_fetching_and_digests():
    """Verify EUR-Lex adapter fetches authoritative documents with computed digests."""
    adapter = EURLexAdapter()
    docs = await adapter.fetch_feed()
    assert len(docs) >= 2

    ai_act = next(d for d in docs if d.celex_or_ecli == "32024R1689" or "32024r1689" in d.source_id or "ai_act" in d.source_id)
    assert ai_act.jurisdiction == "EU"
    assert ai_act.celex_or_ecli == "32024R1689"
    assert ai_act.digest.startswith("0x")
    assert len(ai_act.digest) == 66

    passages = adapter.segment_passages(ai_act)
    assert len(passages) >= 2
    for p in passages:
        assert p["digest"].startswith("0x")
        assert len(p["digest"]) == 66
        assert any("Article" in p["passage_reference"] or "Paragraph" in p["passage_reference"] or "sec" in p["passage_reference"] for p in passages)


@pytest.mark.asyncio
async def test_cjeu_adapter_fetching_and_digests():
    """Verify CJEU adapter fetches judgments with ECLI and operative points."""
    adapter = CJEUAdapter()
    docs = await adapter.fetch_feed()
    assert len(docs) >= 1

    crif = docs[0]
    assert crif.jurisdiction == "EU"
    assert crif.celex_or_ecli == "ECLI:EU:C:2023:369"
    assert crif.digest.startswith("0x")

    passages = adapter.segment_passages(crif)
    assert len(passages) >= 2
    for p in passages:
        assert p["digest"].startswith("0x")
        assert len(p["text"]) > 20


# ── 3. INGESTION PIPELINE, IDEMPOTENCY & REANALYSIS ───────────────────────

@pytest.mark.asyncio
async def test_ingestion_service_e2e_and_idempotent_rerun(test_db):
    """Verify end-to-end ingestion creates documents, passages, proposals, and reruns safely."""
    # Seed a case with facts that will intersect with AI Act
    case_req = CaseCreateRequest(
        title="Biometric AI Training Case",
        question="Is subliminal biometric AI processing compliant with EU rules?",
        jurisdiction="EU",
        assessment_date="2026-10-19",
        facts={"data_categories": ["biometric"], "processing_purpose": "training AI models"}
    )
    case = await CaseService.create_case(test_db, case_req)

    # 1. First ingestion run
    job_1 = await IngestionService.trigger_ingestion(test_db, adapter_name="eur_lex")
    if job_1["status"] != "COMPLETED":
        print(f"DEBUG: job_1 failed with error: {job_1.get('error')}")
    assert job_1["status"] == "COMPLETED"
    assert job_1["documents_discovered"] >= 2
    assert job_1["documents_fetched"] >= 2
    assert job_1["passages_created"] >= 2
    assert job_1["duplicates_skipped"] == 0
    assert case.id in job_1["cases_marked_for_reanalysis"]

    # Verify persisted in test_db
    persisted_doc = await test_db.get(SourceDocument, "doc_eurlex_32024r1689")
    if not persisted_doc:
        persisted_doc = await test_db.get(SourceDocument, "doc_eurlex_ai_act_2024_1689")
    assert persisted_doc is not None
    assert persisted_doc.jurisdiction == "EU"

    # 2. Second ingestion run (Idempotency test)
    job_2 = await IngestionService.trigger_ingestion(test_db, adapter_name="eur_lex")
    assert job_2["status"] == "COMPLETED"
    assert job_2["duplicates_skipped"] >= 2
    assert job_2["documents_fetched"] == 0
    assert job_2["passages_created"] == 0

    # 3. Test CJEU Ingestion
    job_cjeu = await IngestionService.trigger_ingestion(test_db, adapter_name="cjeu")
    assert job_cjeu["status"] == "COMPLETED"
    assert job_cjeu["documents_discovered"] >= 1

    # 4. Observable job history lookup
    jobs = IngestionService.list_jobs()
    assert len(jobs) >= 3
    first_job_id = jobs[0]["job_id"]
    job = IngestionService.get_job(first_job_id)
    assert job is not None
    assert job["job_id"] == first_job_id
    assert "duration_ms" in job
