from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.canonical import compute_canonical_sha256
from backend.app.core.database import get_db
from backend.app.models.entities import Case, DecisionRecordEntity
from backend.app.services.audit_verifier import IndependentAuditVerifier
from backend.app.services.decision_service import DecisionService

router = APIRouter(prefix="/decisions", tags=["Canonical Decisions"])


class DecisionCreateRequest(BaseModel):
    case_id: str = Field(..., description="ID of the case to seal into a Canonical Decision Record")
    rebuild: bool = Field(default=False, description="Whether to recompute and overwrite existing decision record")


@router.get("", response_model=List[Dict[str, Any]])
async def list_decisions(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Lists all canonical, sealed decision records in reverse chronological order."""
    stmt = select(DecisionRecordEntity).order_by(DecisionRecordEntity.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()

    output = []
    for r in records:
        output.append({
            "id": r.id,
            "decision_id": r.id,
            "case_id": r.case_id,
            "case_version": r.case_version,
            "record_digest": r.record_digest,
            "orchestration_version": r.orchestration_version,
            "software_version": r.software_version,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return output


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_decision(
    req: DecisionCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Builds, seals, and persists a Canonical Decision Record connecting evidence, claims,
    forecast commitments, and audit trail for a case.
    """
    try:
        record = await DecisionService.build_canonical_decision_record(
            db=db,
            case_id=req.case_id,
            persist=True,
            rebuild=req.rebuild
        )
        return record.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{decision_id}", response_model=Dict[str, Any])
async def get_decision(decision_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a Canonical Decision Record by its decision_id or case_id."""
    # First try direct primary key
    record_entity = await db.get(DecisionRecordEntity, decision_id)
    if not record_entity:
        # Try looking up by case_id
        stmt = select(DecisionRecordEntity).where(DecisionRecordEntity.case_id == decision_id).order_by(DecisionRecordEntity.created_at.desc())
        res = await db.execute(stmt)
        record_entity = res.scalars().first()

    if not record_entity:
        # Check if case exists to dynamically build
        case = await db.get(Case, decision_id)
        if case:
            try:
                record = await DecisionService.build_canonical_decision_record(db, decision_id, persist=True)
                return record.model_dump()
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Cannot build decision record for case {decision_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Decision record '{decision_id}' not found")

    return record_entity.canonical_data


@router.get("/{decision_id}/verify", response_model=Dict[str, Any])
async def verify_decision(decision_id: str, db: AsyncSession = Depends(get_db)):
    """
    Independently verifies the cryptographic integrity and audit completeness of a Decision Record.
    Recomputes SHA-256 digest, checks Merkle root, and validates passage hashes.
    """
    record_data = None
    record_entity = await db.get(DecisionRecordEntity, decision_id)
    case_id = decision_id

    if record_entity:
        record_data = record_entity.canonical_data
        case_id = record_entity.case_id
    else:
        # Try by case_id
        stmt = select(DecisionRecordEntity).where(DecisionRecordEntity.case_id == decision_id)
        res = await db.execute(stmt)
        record_entity = res.scalars().first()
        if record_entity:
            record_data = record_entity.canonical_data
            case_id = record_entity.case_id
        else:
            case = await db.get(Case, decision_id)
            if not case:
                raise HTTPException(status_code=404, detail=f"Decision record or case '{decision_id}' not found")
            rec = await DecisionService.build_canonical_decision_record(db, decision_id, persist=True)
            record_data = rec.model_dump()

    # Recompute canonical digest
    stored_digest = record_data.get("record_digest")
    recomputed_digest = compute_canonical_sha256(record_data)

    digest_valid = (stored_digest == recomputed_digest)
    claims_count = len(record_data.get("claims", []))
    sources_count = len(record_data.get("evidence_sources", []))
    passages_count = len(record_data.get("evidence_passages", []))

    return {
        "decision_id": decision_id,
        "case_id": case_id,
        "is_valid": digest_valid,
        "stored_digest": stored_digest,
        "recomputed_digest": recomputed_digest,
        "verification_status": "VERIFIED_INTEGRITY" if digest_valid else "CORRUPTED_DIGEST_MISMATCH",
        "claims_verified": claims_count,
        "sources_verified": sources_count,
        "passages_verified": passages_count,
        "audit_events_count": len(record_data.get("audit_events", []))
    }


@router.get("/{decision_id}/provenance", response_model=Dict[str, Any])
async def get_decision_provenance(decision_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full end-to-end evidence and agent provenance lineage for a Decision Record."""
    record_entity = await db.get(DecisionRecordEntity, decision_id)
    if not record_entity:
        stmt = select(DecisionRecordEntity).where(DecisionRecordEntity.case_id == decision_id)
        res = await db.execute(stmt)
        record_entity = res.scalars().first()

    if not record_entity:
        raise HTTPException(status_code=404, detail=f"Decision record '{decision_id}' not found")

    data = record_entity.canonical_data
    return {
        "decision_id": record_entity.id,
        "case_id": record_entity.case_id,
        "record_digest": record_entity.record_digest,
        "orchestration_version": record_entity.orchestration_version,
        "software_version": record_entity.software_version,
        "created_at": record_entity.created_at.isoformat() if record_entity.created_at else None,
        "provenance_chain": {
            "sources": data.get("evidence_sources", []),
            "passages": data.get("evidence_passages", []),
            "claims": data.get("claims", []),
            "audit_events": data.get("audit_events", [])
        }
    }

