import sqlite3
import hashlib
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "veridion.db")


def canonical_json(data) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256(text: str) -> str:
    return "0x" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def migrate_db():
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Check existing columns of audit_events
    cols = [c[1] for c in cursor.execute("PRAGMA table_info(audit_events)").fetchall()]
    print(f"Existing audit_events columns: {cols}")

    if "sequence_number" not in cols:
        print("Adding sequence_number column...")
        cursor.execute("ALTER TABLE audit_events ADD COLUMN sequence_number INTEGER DEFAULT 1")
    if "previous_event_digest" not in cols:
        print("Adding previous_event_digest column...")
        cursor.execute("ALTER TABLE audit_events ADD COLUMN previous_event_digest VARCHAR(66)")
    if "event_digest" not in cols:
        print("Adding event_digest column...")
        cursor.execute("ALTER TABLE audit_events ADD COLUMN event_digest VARCHAR(66)")

    # 2. Check if decision_records table exists
    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "decision_records" not in tables:
        print("Creating decision_records table...")
        cursor.execute("""
            CREATE TABLE decision_records (
                id VARCHAR(64) PRIMARY KEY,
                case_id VARCHAR(64) NOT NULL,
                case_version INTEGER NOT NULL DEFAULT 1,
                orchestration_version VARCHAR(64) NOT NULL,
                software_version VARCHAR(64) NOT NULL,
                record_digest VARCHAR(66) NOT NULL,
                canonical_data JSON NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (case_id) REFERENCES cases(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_case_id ON decision_records (case_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_decision_records_record_digest ON decision_records (record_digest)")

    # 3. Populate sequence_number, previous_event_digest, and event_digest for existing audit_events
    print("Backfilling hash-chain for existing audit_events...")
    # Fetch distinct case_ids
    case_ids = [r[0] for r in cursor.execute("SELECT DISTINCT case_id FROM audit_events").fetchall()]
    print(f"Found {len(case_ids)} distinct cases in audit_events.")

    GENESIS_DIGEST = "0x" + "0" * 64
    updated_total = 0

    for cid in case_ids:
        # Fetch events ordered by timestamp asc, then id asc
        events = cursor.execute(
            "SELECT id, case_id, event_type, actor, payload_digest, payload, tx_hash, timestamp "
            "FROM audit_events WHERE case_id = ? ORDER BY timestamp ASC, id ASC",
            (cid,)
        ).fetchall()

        prev_digest = GENESIS_DIGEST
        for seq, ev in enumerate(events, start=1):
            ev_id, case_id, event_type, actor, payload_digest, payload, tx_hash, timestamp = ev
            # Recompute payload_digest if needed
            if not payload_digest or not payload_digest.startswith("0x"):
                p_obj = json.loads(payload) if isinstance(payload, str) else (payload or {})
                payload_digest = compute_sha256(canonical_json(p_obj))

            # Canonical representation of event linkage:
            link_record = {
                "actor": actor,
                "case_id": case_id,
                "event_type": event_type,
                "payload_digest": payload_digest,
                "previous_event_digest": prev_digest,
                "sequence_number": seq,
                "timestamp": str(timestamp),
                "tx_hash": tx_hash or ""
            }
            ev_digest = compute_sha256(canonical_json(link_record))

            cursor.execute(
                "UPDATE audit_events SET sequence_number = ?, previous_event_digest = ?, "
                "payload_digest = ?, event_digest = ? WHERE id = ?",
                (seq, prev_digest, payload_digest, ev_digest, ev_id)
            )
            prev_digest = ev_digest
            updated_total += 1

    conn.commit()
    print(f"Successfully migrated and hash-chained {updated_total} audit events!")
    conn.close()


if __name__ == "__main__":
    migrate_db()
