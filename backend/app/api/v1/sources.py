from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.entities import SourceDocument, EvidencePassage
from backend.app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/sources", tags=["Sources & Retrieval"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_sources(
    provenance: Optional[str] = Query(None, description="Filter by provenance (e.g. REMOTE_OFFICIAL_SOURCE, BUNDLED_FIXTURE)"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction, e.g. EU, California"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all legal source documents with explicit provenance, authority metadata,
    cryptographic digest, and passage count.
    """
    stmt = select(SourceDocument).order_by(SourceDocument.retrieved_at.desc())
    if provenance:
        stmt = stmt.where(SourceDocument.provenance == provenance)
    if jurisdiction:
        stmt = stmt.where(SourceDocument.jurisdiction == jurisdiction)

    result = await db.execute(stmt)
    docs = result.scalars().all()

    output = []
    for d in docs:
        p_stmt = select(EvidencePassage.id).where(EvidencePassage.document_id == d.id)
        p_res = await db.execute(p_stmt)
        passage_count = len(p_res.scalars().all())

        output.append({
            "id": d.id,
            "title": d.title,
            "authority": d.authority,
            "jurisdiction": d.jurisdiction,
            "url": d.url,
            "publication_date": d.publication_date,
            "effective_date": d.effective_date,
            "version": d.version,
            "digest": d.digest,
            "provenance": d.provenance or "BUNDLED_FIXTURE",
            "retrieved_at": d.retrieved_at.isoformat() if d.retrieved_at else None,
            "passage_count": passage_count
        })
    return output


@router.get("/passages", response_model=List[Dict[str, Any]])
async def search_passages(
    q: str = Query(..., min_length=2, description="Search query or legal keywords"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction, e.g. EU, California"),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Search curated legal corpus passages with provenance, authority metadata, and cryptographic digests (FR-008).
    """
    return await RetrievalService.retrieve_passages(
        db=db,
        query=q,
        jurisdiction=jurisdiction,
        limit=limit
    )


@router.get("/passages/{evidence_id}", response_model=Optional[Dict[str, Any]])
async def get_passage(evidence_id: str, db: AsyncSession = Depends(get_db)):
    """Reads a single passage by stable identifier with full provenance."""
    return await RetrievalService.get_passage_by_id(db, evidence_id)


@router.get("/{source_id}", response_model=Dict[str, Any])
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    """Reads a single source document by ID with authority metadata and passage count."""
    doc = await db.get(SourceDocument, source_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Source document '{source_id}' not found")
    p_stmt = select(EvidencePassage.id).where(EvidencePassage.document_id == doc.id)
    p_res = await db.execute(p_stmt)
    passage_count = len(p_res.scalars().all())
    return {
        "id": doc.id,
        "title": doc.title,
        "authority": doc.authority,
        "jurisdiction": doc.jurisdiction,
        "url": doc.url,
        "publication_date": doc.publication_date,
        "effective_date": doc.effective_date,
        "version": doc.version,
        "digest": doc.digest,
        "provenance": doc.provenance or "BUNDLED_FIXTURE",
        "retrieved_at": doc.retrieved_at.isoformat() if doc.retrieved_at else None,
        "passage_count": passage_count
    }


@router.get("/{source_id}/passages", response_model=List[Dict[str, Any]])
async def get_source_passages(source_id: str, db: AsyncSession = Depends(get_db)):
    """Lists all extracted evidence passages associated with a legal source document."""
    doc = await db.get(SourceDocument, source_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Source document '{source_id}' not found")
    p_stmt = select(EvidencePassage).where(EvidencePassage.document_id == source_id)
    p_res = await db.execute(p_stmt)
    passages = p_res.scalars().all()
    return [
        {
            "id": p.id,
            "evidence_id": p.id,
            "passage_reference": p.passage_reference,
            "text": p.text,
            "digest": p.digest,
            "jurisdiction": p.jurisdiction,
            "authority": doc.authority,
            "provenance": doc.provenance or "BUNDLED_FIXTURE",
            "effective_date": doc.effective_date,
            "url": doc.url
        }
        for p in passages
    ]


@router.post("/search", response_model=List[Dict[str, Any]])
async def search_sources_post(
    query: str = Query(..., min_length=2),
    jurisdiction: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Searches legal passages with term matching and cosine ranking."""
    return await RetrievalService.retrieve_passages(db=db, query=query, jurisdiction=jurisdiction, limit=limit)


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_sources(db: AsyncSession = Depends(get_db)):
    """Refreshes official regulatory sources from bundled authoritative gazette definitions."""
    count = await RetrievalService.initialize_corpus(db)
    return {
        "status": "REFRESHED",
        "documents_initialized": count,
        "providers_checked": ["EUR_LEX", "CJEU", "EDPB"]
    }
