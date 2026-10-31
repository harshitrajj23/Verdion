from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.entities import Case, Claim, ClaimEvidenceLink, EvidencePassage, SourceDocument
from backend.app.schemas.agent import ClaimGroundingResult, ClaimOutput, EvidenceRef
from backend.app.services.grounding_service import EvidenceGroundingService

router = APIRouter(prefix="/evidence", tags=["Evidence & Grounding"])


class EvidenceVerifyRequest(BaseModel):
    claim_id: Optional[str] = None
    claim_text: str = Field(..., description="Legal claim proposition to verify")
    evidence_refs: List[EvidenceRef] = Field(..., description="Cited evidence passages with SHA-256 digests")
    case_facts: Dict[str, Any] = Field(default_factory=dict, description="Facts of the case")
    case_jurisdiction: str = Field(default="EU", description="Declared jurisdiction of evaluation")
    assessment_date: Optional[str] = Field(None, description="ISO date of assessment (e.g. 2026-10-31)")


@router.get("", response_model=List[Dict[str, Any]])
async def list_evidence(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction (EU, California)"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Lists verified evidence passages with source provenance and cryptographic digests."""
    stmt = select(EvidencePassage).limit(limit)
    if jurisdiction:
        stmt = stmt.where(EvidencePassage.jurisdiction == jurisdiction)

    res = await db.execute(stmt)
    passages = res.scalars().all()

    output = []
    for p in passages:
        doc = await db.get(SourceDocument, p.document_id) if p.document_id else None
        output.append({
            "id": p.id,
            "evidence_id": p.id,
            "passage_reference": p.passage_reference,
            "digest": p.digest,
            "text": p.text,
            "jurisdiction": p.jurisdiction,
            "document_id": p.document_id,
            "authority": doc.authority if doc else "EU Regulation",
            "provenance": doc.provenance if doc else "BUNDLED_FIXTURE",
            "effective_date": doc.effective_date if doc else None,
            "url": doc.url if doc else None
        })
    return output


@router.get("/{evidence_id}", response_model=Dict[str, Any])
async def get_evidence(evidence_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a single evidence passage by ID with full source authority metadata."""
    passage = await db.get(EvidencePassage, evidence_id)
    if not passage:
        raise HTTPException(status_code=404, detail=f"Evidence passage '{evidence_id}' not found")

    doc = await db.get(SourceDocument, passage.document_id) if passage.document_id else None
    return {
        "id": passage.id,
        "evidence_id": passage.id,
        "passage_reference": passage.passage_reference,
        "digest": passage.digest,
        "text": passage.text,
        "jurisdiction": passage.jurisdiction,
        "document_id": passage.document_id,
        "authority": doc.authority if doc else "EU Regulation",
        "provenance": doc.provenance if doc else "BUNDLED_FIXTURE",
        "effective_date": doc.effective_date if doc else None,
        "url": doc.url if doc else None
    }


@router.post("/verify", response_model=ClaimGroundingResult)
async def verify_evidence_grounding(
    req: EvidenceVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates claim evidence grounding across all 9 discrete dimensions (Option C):
    PASSAGE_INTEGRITY, SOURCE_AUTHENTICITY, CITATION_VALIDITY, QUOTATION_ACCURACY,
    SEMANTIC_SUPPORT, LEGAL_ENTAILMENT, FACT_TO_LAW_APPLICABILITY, JURISDICTIONAL_VALIDITY, TEMPORAL_VALIDITY.
    """
    # Fetch passages from db matching requested refs
    passages = []
    for ref in req.evidence_refs:
        p = await db.get(EvidencePassage, ref.evidence_id)
        if p:
            doc = await db.get(SourceDocument, p.document_id) if p.document_id else None
            passages.append({
                "id": p.id,
                "passage_reference": p.passage_reference,
                "text": p.text,
                "digest": p.digest,
                "jurisdiction": p.jurisdiction,
                "authority": doc.authority if doc else "EU Regulation",
                "provenance": doc.provenance if doc else "BUNDLED_FIXTURE",
                "effective_date": doc.effective_date if doc else None
            })
        else:
            # Fallback placeholder passage for testing unknown IDs
            passages.append({
                "id": ref.evidence_id,
                "passage_reference": ref.passage_reference,
                "text": "",
                "digest": ref.digest,
                "jurisdiction": req.case_jurisdiction,
                "authority": "",
                "provenance": "UNVERIFIED"
            })

    claim_obj = ClaimOutput(
        claim_id=req.claim_id or "CLM-VERIFY",
        claim_text=req.claim_text,
        claim_type="STATUTORY_INTERPRETATION",
        confidence=0.90,
        confidence_rationale="Evaluated via 9-dimensional evidence grounding service",
        evidence_refs=req.evidence_refs
    )

    return EvidenceGroundingService.evaluate_claim_grounding(
        claim=claim_obj,
        passages=passages,
        case_facts=req.case_facts,
        case_jurisdiction=req.case_jurisdiction,
        assessment_date=req.assessment_date
    )

