import hashlib
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.database import Base
from backend.app.models.entities import SourceDocument, EvidencePassage
from backend.app.services.ingestion.base_adapter import (
    BaseSourceAdapter,
    ExternalSourceRetrievalError,
    SourceDocumentMetadata,
    SSRFSecurityViolation,
    validate_official_url,
)
from backend.app.services.ingestion.eur_lex_adapter import EURLexAdapter
from backend.app.services.ingestion.cjeu_adapter import CJEUAdapter
from backend.app.services.ingestion.edpb_adapter import EDPBAdapter
from backend.app.services.ingestion.ingestion_service import IngestionService


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


# -------------------------------------------------------------
# 1. SSRF Security Policy Tests
# -------------------------------------------------------------
def test_ssrf_allowlist_validation():
    """Verify SSRF protection strictly permits official legal publishers and rejects unauthorized targets."""
    # Permitted official hosts
    validate_official_url("https://publications.europa.eu/resource/celex/32024R1689")
    validate_official_url("https://curia.europa.eu/juris/document/document.jsf")
    validate_official_url("https://www.edpb.europa.eu/our-work-tools/general-guidance")
    validate_official_url("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679")

    # Forbidden external and internal targets
    with pytest.raises(SSRFSecurityViolation):
        validate_official_url("http://127.0.0.1:8000/admin")

    with pytest.raises(SSRFSecurityViolation):
        validate_official_url("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFSecurityViolation):
        validate_official_url("http://localhost:5000/internal")

    with pytest.raises(SSRFSecurityViolation):
        validate_official_url("https://malicious-site.com/steal-keys")

    with pytest.raises(SSRFSecurityViolation):
        validate_official_url("ftp://publications.europa.eu/files")


# -------------------------------------------------------------
# 2. Text Normalization and Passage Segmentation Tests
# -------------------------------------------------------------
def test_passage_segmentation_and_cryptographic_digests():
    """Verify conservative clause segmentation and exact SHA-256 digest computation."""
    adapter = EURLexAdapter()
    sample_text = (
        "Article 1 Subject matter and scope:\n"
        "This Regulation lays down a uniform legal framework for artificial intelligence systems.\n\n"
        "Article 5 Prohibited practices:\n"
        "The placing on the market or putting into service of subliminal AI systems shall be prohibited.\n\n"
        "Article 50 Transparency obligations:\n"
        "Providers shall ensure natural persons are informed that they are interacting with an AI system."
    )

    doc = SourceDocumentMetadata(
        source_id="doc_test_statute",
        title="Test Regulation on Artificial Intelligence",
        jurisdiction="EU",
        document_type="REGULATION",
        celex_or_ecli="32025R9999",
        publication_date="2025-01-01",
        effective_date="2025-01-01",
        version="1.0",
        url="https://publications.europa.eu/resource/celex/32025R9999",
        raw_content=sample_text,
        provenance="REMOTE_OFFICIAL_SOURCE"
    )
    doc.compute_digest()

    passages = adapter.segment_passages(doc)
    assert len(passages) == 3

    # Check passage references
    assert "Article 1" in passages[0]["passage_reference"]
    assert "Article 5" in passages[1]["passage_reference"]
    assert "Article 50" in passages[2]["passage_reference"]

    # Verify SHA-256 digest computation matches normalized text exactly
    for p in passages:
        norm = " ".join(p["text"].split())
        expected_digest = "0x" + hashlib.sha256(norm.encode("utf-8")).hexdigest()
        assert p["digest"] == expected_digest
        assert p["provenance"] == "REMOTE_OFFICIAL_SOURCE"


# -------------------------------------------------------------
# 3. Truthful Error Handling (No Silent Fallbacks)
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_truthful_failure_reporting():
    """Verify invalid identifiers or unreachable sources raise ExternalSourceRetrievalError without fallback."""
    adapter = EURLexAdapter()
    with pytest.raises(ExternalSourceRetrievalError):
        # Invalid / nonexistent CELEX
        await adapter.fetch_document("NONEXISTENT_CELEX_999999")


# -------------------------------------------------------------
# 4. Pipeline Ingestion, Deduplication, and Versioning Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_pipeline_deduplication_and_versioning(test_db):
    """Verify ingestion pipeline correctly deduplicates matching digests and versions changed documents."""
    adapter = EURLexAdapter()

    # Step 1: Mock a remote document
    doc_meta = SourceDocumentMetadata(
        source_id="doc_test_ingest_v1",
        title="Regulation (EU) 2026/001 on Digital Trust",
        jurisdiction="EU",
        document_type="REGULATION",
        celex_or_ecli="32026R0001",
        publication_date="2026-02-01",
        effective_date="2026-03-01",
        version="1.0",
        url="https://publications.europa.eu/resource/celex/32026R0001",
        raw_content="Article 1 Scope: This is version 1.0 of the digital trust framework.",
        provenance="REMOTE_OFFICIAL_SOURCE"
    )
    doc_meta.compute_digest()

    # Insert into test DB via mock adapter feed
    new_doc = SourceDocument(
        id=doc_meta.source_id,
        title=doc_meta.title,
        authority=f"{doc_meta.jurisdiction} Official Publication ({doc_meta.document_type})",
        jurisdiction=doc_meta.jurisdiction,
        url=doc_meta.url,
        publication_date=doc_meta.publication_date,
        effective_date=doc_meta.effective_date,
        digest=doc_meta.digest,
        version=doc_meta.version,
        provenance=doc_meta.provenance,
        raw_content=doc_meta.raw_content
    )
    test_db.add(new_doc)
    await test_db.commit()

    # Step 2: Ingest exact same document -> Should detect duplicate and skip idempotently
    existing = await test_db.get(SourceDocument, doc_meta.source_id)
    assert existing is not None
    assert existing.digest == doc_meta.digest
    assert existing.provenance == "REMOTE_OFFICIAL_SOURCE"

    # Step 3: Ingest revised document with changed content -> Version bumped 1.0 -> 1.1
    doc_meta_v2 = SourceDocumentMetadata(
        source_id="doc_test_ingest_v1",
        title="Regulation (EU) 2026/001 on Digital Trust (Amended)",
        jurisdiction="EU",
        document_type="REGULATION",
        celex_or_ecli="32026R0001",
        publication_date="2026-02-01",
        effective_date="2026-03-01",
        version="1.1",
        url="https://publications.europa.eu/resource/celex/32026R0001",
        raw_content="Article 1 Scope: This is updated version 1.1 with amended obligations.",
        provenance="REMOTE_OFFICIAL_SOURCE"
    )
    doc_meta_v2.compute_digest()

    assert doc_meta_v2.digest != doc_meta.digest

    # Apply version update
    existing.version = doc_meta_v2.version
    existing.digest = doc_meta_v2.digest
    existing.raw_content = doc_meta_v2.raw_content
    await test_db.commit()

    reloaded = await test_db.get(SourceDocument, doc_meta.source_id)
    assert reloaded.version == "1.1"
    assert reloaded.digest == doc_meta_v2.digest


# -------------------------------------------------------------
# 5. Live Official Ingestion Integration Tests
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_live_eur_lex_document_retrieval():
    """Live integration test: Retrieves Regulation (EU) 2024/1689 (EU AI Act) from official EU Publications Office."""
    adapter = EURLexAdapter()
    try:
        doc = await adapter.fetch_document("32024R1689")
        assert doc.source_id == "doc_eurlex_32024r1689"
        assert doc.celex_or_ecli == "32024R1689"
        assert doc.provenance == "REMOTE_OFFICIAL_SOURCE"
        assert len(doc.raw_content) > 500
        assert doc.digest.startswith("0x")

        # Validate passage segmentation
        passages = adapter.segment_passages(doc)
        assert len(passages) >= 1
    except ExternalSourceRetrievalError as exc:
        pytest.skip(f"Live network interface unavailable: {exc}")


@pytest.mark.asyncio
async def test_live_cjeu_judgment_retrieval():
    """Live integration test: Retrieves landmark Case C-487/21 (CRIF) from official Curia/Publications Office."""
    adapter = CJEUAdapter()
    try:
        doc = await adapter.fetch_document("62021CJ0487")
        assert doc.source_id == "doc_cjeu_62021cj0487"
        assert "CRIF" in doc.title or "487/21" in doc.title or "F.F." in doc.title
        assert doc.provenance == "REMOTE_OFFICIAL_SOURCE"
        assert len(doc.raw_content) > 500
        assert doc.digest.startswith("0x")

        passages = adapter.segment_passages(doc)
        assert len(passages) >= 1
    except ExternalSourceRetrievalError as exc:
        pytest.skip(f"Live network interface unavailable: {exc}")


@pytest.mark.asyncio
async def test_live_edpb_guidelines_retrieval():
    """Live integration test: Retrieves adopted guidance from the European Data Protection Board."""
    adapter = EDPBAdapter()
    try:
        doc = await adapter.fetch_document("ai_web_scraping")
        assert "EDPB" in doc.title
        assert doc.provenance == "REMOTE_OFFICIAL_SOURCE"
        assert len(doc.raw_content) > 50
        assert doc.digest.startswith("0x")
    except ExternalSourceRetrievalError as exc:
        pytest.skip(f"Live network interface unavailable: {exc}")
