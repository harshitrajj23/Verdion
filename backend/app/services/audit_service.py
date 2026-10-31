import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.canonical import (
    compute_canonical_sha256,
    format_canonical_timestamp,
    serialize_canonical_json,
)
from backend.app.models.entities import AuditEvent, utcnow

GENESIS_PREVIOUS_DIGEST = "0x" + "0" * 64


class AuditService:
    @staticmethod
    def compute_event_digest(
        sequence_number: int,
        case_id: str,
        event_type: str,
        actor: str,
        payload_digest: str,
        previous_event_digest: str,
        timestamp_str: str,
        tx_hash: Optional[str] = None
    ) -> str:
        """
        Canonical hash of an audit event linking sequence, event properties, and previous digest.
        """
        link_record = {
            "actor": actor,
            "case_id": case_id,
            "event_type": event_type,
            "payload_digest": payload_digest,
            "previous_event_digest": previous_event_digest,
            "sequence_number": sequence_number,
            "timestamp": timestamp_str,
            "tx_hash": tx_hash or ""
        }
        return compute_canonical_sha256(link_record)

    @staticmethod
    def compute_merkle_root(leaf_digests: List[str], hardened: bool = False) -> str:
        """
        Computes binary Merkle tree root of an ordered list of digests.
        If hardened=True, applies RFC 6962 domain separation (0x00 for leaves, 0x01 for interior nodes)
        and promotes odd nodes without duplicating (preventing Bitcoin CVE-2012-2459).
        If hardened=False (default for legacy compatibility), uses the legacy binary duplication tree.
        If empty, returns GENESIS_PREVIOUS_DIGEST.
        """
        if not leaf_digests:
            return GENESIS_PREVIOUS_DIGEST

        if hardened:
            return AuditService.compute_hardened_merkle_root(leaf_digests)

        current_layer = [
            bytes.fromhex(d[2:] if d.startswith("0x") else d) for d in leaf_digests
        ]
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i + 1] if i + 1 < len(current_layer) else left
                combined = hashlib.sha256(left + right).digest()
                next_layer.append(combined)
            current_layer = next_layer
        return "0x" + current_layer[0].hex()

    @staticmethod
    def compute_hardened_merkle_root(leaf_digests: List[str]) -> str:
        """
        Hardened RFC 6962-style Merkle Tree:
        - Domain separation:
            leaf_hash = SHA256(0x00 || leaf_digest)
            node_hash = SHA256(0x01 || left || right)
        - Odd-node promotion: Unpaired right node is promoted to next layer without duplication,
          preventing CVE-2012-2459 duplicate-leaf collisions.
        """
        if not leaf_digests:
            return GENESIS_PREVIOUS_DIGEST

        # Leaf layer with 0x00 prefix
        current_layer = [
            hashlib.sha256(b"\x00" + bytes.fromhex(d[2:] if d.startswith("0x") else d)).digest()
            for d in leaf_digests
        ]

        while len(current_layer) > 1:
            next_layer = []
            i = 0
            while i < len(current_layer):
                if i + 1 < len(current_layer):
                    left = current_layer[i]
                    right = current_layer[i + 1]
                    # Interior node with 0x01 prefix
                    combined = hashlib.sha256(b"\x01" + left + right).digest()
                    next_layer.append(combined)
                    i += 2
                else:
                    # Promote odd node without duplication (CVE-2012-2459 fix)
                    next_layer.append(current_layer[i])
                    i += 1
            current_layer = next_layer

        return "0x" + current_layer[0].hex()

    @staticmethod
    async def log_event(
        db: AsyncSession,
        case_id: str,
        event_type: str,
        actor: str,
        payload: Dict[str, Any],
        tx_hash: Optional[str] = None
    ) -> AuditEvent:
        """
        Appends an immutable audit event with canonical payload digest and previous-event hash link.
        """
        # Determine sequence number and previous digest for this case
        stmt_last = (
            select(AuditEvent)
            .where(AuditEvent.case_id == case_id)
            .order_by(AuditEvent.sequence_number.desc(), AuditEvent.timestamp.desc())
            .limit(1)
        )
        res = await db.execute(stmt_last)
        last_event = res.scalars().first()

        if last_event and last_event.event_digest:
            sequence_number = (last_event.sequence_number or 0) + 1
            prev_digest = last_event.event_digest
        elif last_event:
            sequence_number = (last_event.sequence_number or 1) + 1
            prev_digest = last_event.payload_digest or GENESIS_PREVIOUS_DIGEST
        else:
            sequence_number = 1
            prev_digest = GENESIS_PREVIOUS_DIGEST

        # Canonical payload digest
        payload_digest = compute_canonical_sha256(payload)
        now_dt = utcnow()
        timestamp_str = format_canonical_timestamp(now_dt)

        # Compute full event digest linking back to prev_digest
        event_digest = AuditService.compute_event_digest(
            sequence_number=sequence_number,
            case_id=case_id,
            event_type=event_type,
            actor=actor,
            payload_digest=payload_digest,
            previous_event_digest=prev_digest,
            timestamp_str=timestamp_str,
            tx_hash=tx_hash
        )

        event = AuditEvent(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            sequence_number=sequence_number,
            event_type=event_type,
            actor=actor,
            payload_digest=payload_digest,
            payload=payload,
            previous_event_digest=prev_digest,
            event_digest=event_digest,
            tx_hash=tx_hash,
            timestamp=now_dt
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_case_audit_trail(
        db: AsyncSession,
        case_id: str,
        limit: int = 200
    ) -> List[AuditEvent]:
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.case_id == case_id)
            .order_by(AuditEvent.sequence_number.asc(), AuditEvent.timestamp.asc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def verify_case_audit_chain(
        db: AsyncSession,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Independently audits the append-only event chain for a case.
        Verifies:
        1. Monotonic sequence numbering without gaps
        2. Accurate canonical payload digests matching event payload
        3. Strict previous_event_digest continuity linking back to genesis
        4. Recomputed event_digest matching recorded digest
        5. Computes current Merkle root checkpoint
        """
        events = await AuditService.get_case_audit_trail(db, case_id, limit=1000)
        return AuditService.verify_events_list(events, case_id)

    @staticmethod
    def verify_events_list(events: List[AuditEvent], case_id: str) -> Dict[str, Any]:
        """Validates an ordered list of audit events."""
        if not events:
            return {
                "case_id": case_id,
                "is_valid": True,
                "status": "EMPTY",
                "events_verified": 0,
                "chain_head_digest": None,
                "merkle_checkpoint_root": GENESIS_PREVIOUS_DIGEST,
                "errors": []
            }

        errors = []
        expected_prev = GENESIS_PREVIOUS_DIGEST
        verified_count = 0
        event_digests = []

        for idx, ev in enumerate(events):
            expected_seq = idx + 1
            # Check sequence continuity
            if ev.sequence_number != expected_seq:
                errors.append(
                    f"Sequence discontinuity at event {ev.id}: expected {expected_seq}, found {ev.sequence_number}"
                )

            # Check payload digest
            computed_payload_digest = compute_canonical_sha256(ev.payload or {})
            if ev.payload_digest != computed_payload_digest:
                errors.append(
                    f"Payload tampering detected at event {ev.id} (seq {ev.sequence_number}): "
                    f"recorded {ev.payload_digest}, computed {computed_payload_digest}"
                )

            # Check previous digest linkage
            if ev.previous_event_digest != expected_prev:
                errors.append(
                    f"Broken hash chain link at event {ev.id} (seq {ev.sequence_number}): "
                    f"recorded prev {ev.previous_event_digest}, expected {expected_prev}"
                )

            # Check recomputed event digest
            ts_str = format_canonical_timestamp(ev.timestamp)
            computed_event_digest = AuditService.compute_event_digest(
                sequence_number=ev.sequence_number,
                case_id=ev.case_id,
                event_type=ev.event_type,
                actor=ev.actor,
                payload_digest=computed_payload_digest,
                previous_event_digest=ev.previous_event_digest,
                timestamp_str=ts_str,
                tx_hash=ev.tx_hash
            )

            if ev.event_digest and ev.event_digest != computed_event_digest:
                errors.append(
                    f"Event digest mismatch at event {ev.id} (seq {ev.sequence_number}): "
                    f"recorded {ev.event_digest}, recomputed {computed_event_digest}"
                )

            expected_prev = ev.event_digest or computed_event_digest
            event_digests.append(expected_prev)
            verified_count += 1

        is_valid = len(errors) == 0
        merkle_root = AuditService.compute_merkle_root(event_digests)

        return {
            "case_id": case_id,
            "is_valid": is_valid,
            "status": "VERIFIED" if is_valid else "FAILED",
            "events_verified": verified_count,
            "chain_head_digest": event_digests[-1] if event_digests else None,
            "merkle_checkpoint_root": merkle_root,
            "errors": errors
        }
