from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.entities import AuditEvent
from backend.app.schemas.audit import AuditEventResponse
from backend.app.services.audit_service import AuditService
from backend.app.services.audit_verifier import IndependentAuditVerifier
from backend.app.services.decision_service import DecisionService

router = APIRouter(prefix="/audit", tags=["Audit & Provenance"])


@router.get("", response_model=List[AuditEventResponse])
async def list_audit_events(
    case_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Returns chronologically ordered protocol lifecycle audit events with payload digests and hash chain links (FR-054)."""
    stmt = select(AuditEvent)
    if case_id:
        stmt = stmt.where(AuditEvent.case_id == case_id)
    stmt = stmt.order_by(AuditEvent.sequence_number.asc(), AuditEvent.timestamp.asc()).limit(limit)

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/chain/{case_id}")
async def verify_audit_chain(
    case_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verifies the append-only cryptographic event chain for a case.
    Checks sequence continuity, payload digests, previous-digest linkage, and Merkle checkpoint root.
    """
    result = await AuditService.verify_case_audit_chain(db, case_id)
    return result


@router.get("/decision-record/{case_id}")
async def get_case_decision_record(
    case_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieves or generates the canonical, auditable decision record for a case.
    """
    try:
        record = await DecisionService.build_canonical_decision_record(db, case_id, persist=True)
        return record.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/package/{case_id}")
async def export_audit_package(
    case_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generates an exportable self-contained JSON audit package for independent offline verification.
    """
    try:
        package = await DecisionService.generate_audit_package(db, case_id)
        return package
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/verify-package")
async def verify_uploaded_audit_package(
    package_data: Dict[str, Any] = Body(...),
    trusted_checkpoint: Optional[str] = Query(None, description="Optional trusted external Merkle root checkpoint")
) -> Dict[str, Any]:
    """
    Independent audit verification endpoint.
    Validates any uploaded or exported VERIDION audit package offline.
    """
    report = IndependentAuditVerifier.verify_audit_package(package_data, trusted_checkpoint=trusted_checkpoint)
    return report



@router.get("/events", response_model=List[AuditEventResponse])
async def list_audit_events_alias(
    case_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Alias for /audit listing lifecycle audit events."""
    return await list_audit_events(case_id=case_id, limit=limit, db=db)


@router.get("/verify")
async def verify_audit_query(
    case_id: str = Query(..., description="Case ID to verify audit chain for"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Verifies the append-only cryptographic event chain and Merkle root for a given case."""
    return await AuditService.verify_case_audit_chain(db, case_id)


@router.get("/records/{record_id}", response_model=Dict[str, Any])
async def get_audit_record(record_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves an individual audit event record by event_id or sequence identifier."""
    event = await db.get(AuditEvent, record_id)
    if not event:
        # Try sequence number
        if record_id.isdigit():
            stmt = select(AuditEvent).where(AuditEvent.sequence_number == int(record_id))
            res = await db.execute(stmt)
            event = res.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Audit record '{record_id}' not found")
    return {
        "id": event.id,
        "sequence_number": event.sequence_number,
        "case_id": event.case_id,
        "event_type": event.event_type,
        "actor": event.actor,
        "payload": event.payload,
        "event_digest": event.event_digest,
        "previous_digest": event.previous_digest,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None
    }
