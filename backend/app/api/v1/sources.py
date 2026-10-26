from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/sources", tags=["Sources & Retrieval"])


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
