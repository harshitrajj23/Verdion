from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.entities import SourceDocument, EvidencePassage
from backend.app.services.ingestion.ingestion_service import IngestionService

router = APIRouter(prefix="/ingestion", tags=["Regulatory Ingestion"])


@router.post("/trigger", status_code=status.HTTP_200_OK)
async def trigger_ingestion(
    adapter: str = Query("eur_lex", description="Source adapter to trigger ('eur_lex', 'cjeu', or 'edpb')"),
    identifier: Optional[str] = Query(None, description="Optional specific identifier (CELEX, ECLI, or EDPB slug)"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Triggers an official legal source ingestion run.
    Retrieves live documents from official external publishers (EUR-Lex, CJEU, EDPB),
    validates SSRF allowlist, checks cryptographic digests for version changes,
    segments clauses into verified passages, and records immutable audit events.
    """
    try:
        job_result = await IngestionService.trigger_ingestion(
            db,
            adapter_name=adapter,
            identifier=identifier
        )
        return job_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_ingestion_jobs() -> List[Dict[str, Any]]:
    """Returns historical log and telemetry of all background ingestion jobs."""
    return IngestionService.list_jobs()


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_ingestion_job(job_id: str) -> Dict[str, Any]:
    """Returns telemetry for a specific ingestion job."""
    job = IngestionService.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job


@router.get("/proposals", response_model=List[Dict[str, Any]])
async def list_reanalysis_proposals() -> List[Dict[str, Any]]:
    """
    Returns cases flagged for re-analysis due to newly ingested statutory provisions,
    amendments, or CJEU jurisprudence.
    """
    return IngestionService.list_proposals()


@router.get("/sources", response_model=List[Dict[str, Any]])
async def list_legal_sources(
    provenance: Optional[str] = Query(None, description="Filter by provenance (e.g. REMOTE_OFFICIAL_SOURCE, BUNDLED_FIXTURE)"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction (e.g. EU, CA)"),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Lists all persisted legal sources with their explicit provenance classification,
    cryptographic digest, official identifier, and passage count.
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
        # Count passages
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


@router.get("/sources/{source_id}", response_model=Dict[str, Any])
async def get_legal_source_detail(
    source_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Returns detailed legal source metadata, its verbatim content preview, and segmented passages."""
    doc = await db.get(SourceDocument, source_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Legal source '{source_id}' not found.")

    p_stmt = select(EvidencePassage).where(EvidencePassage.document_id == doc.id).order_by(EvidencePassage.passage_reference)
    p_res = await db.execute(p_stmt)
    passages = p_res.scalars().all()

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
        "raw_content_preview": doc.raw_content[:2000] if doc.raw_content else "",
        "passages": [
            {
                "id": p.id,
                "passage_reference": p.passage_reference,
                "content_reference": p.content_reference,
                "text": p.text,
                "digest": p.digest,
                "source_version": p.source_version,
                "provenance": p.provenance or doc.provenance or "BUNDLED_FIXTURE"
            }
            for p in passages
        ]
    }
