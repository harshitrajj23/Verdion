from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.entities import AuditEvent
from backend.app.schemas.audit import AuditEventResponse

router = APIRouter(prefix="/audit", tags=["Audit & Provenance"])


@router.get("", response_model=List[AuditEventResponse])
async def list_audit_events(
    case_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Returns chronologically ordered protocol lifecycle audit events with payload digests (FR-054)."""
    stmt = select(AuditEvent)
    if case_id:
        stmt = stmt.where(AuditEvent.case_id == case_id)
    stmt = stmt.order_by(AuditEvent.timestamp.desc()).limit(limit)

    res = await db.execute(stmt)
    return list(res.scalars().all())
