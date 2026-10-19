import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.crypto import compute_sha256_digest
from backend.app.models.entities import AuditEvent, utcnow


class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        case_id: str,
        event_type: str,
        actor: str,
        payload: Dict[str, Any],
        tx_hash: Optional[str] = None
    ) -> AuditEvent:
        """Appends an immutable audit event with canonical payload digest."""
        digest = compute_sha256_digest(payload)
        event = AuditEvent(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            payload_digest=digest,
            payload=payload,
            tx_hash=tx_hash,
            timestamp=utcnow()
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_case_audit_trail(
        db: AsyncSession,
        case_id: str,
        limit: int = 100
    ) -> List[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.case_id == case_id)
            .order_by(AuditEvent.timestamp.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
