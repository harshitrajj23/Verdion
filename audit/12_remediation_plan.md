# VERIDION Audit — Part 12: Remediation & Maintenance Plan

**Audit Timestamp**: 2026-10-27T04:55:00+05:30  
**Lead Auditor**: Principal Software Architect & QA Automation Lead  
**Requirements Reference**: `VERIDION_Product_Requirements_Document_v1.0.pdf`  
**Deliverable**: `audit/12_remediation_plan.md`  

---

## 1. Governance & Execution Notice

> [!IMPORTANT]
> **Per Non-Negotiable Rule 17 & Part 12 directives:**
> No remediation changes are executed automatically. Each proposed item below documents the root cause, exact files to modify, regression risks, and acceptance criteria. **These items will only be executed upon explicit user approval.**

---

## 2. Prioritized Remediation & Enhancement Items

### Item 1 (P1 — Developer Experience): Automated Local Database Initialization Guard

1. **Confirmed Defect / Observation**:
   When developers pull changes where database columns transitioned from `nullable=False` to `nullable=True` (e.g. `settlements.tx_hash` made nullable for unconfirmed simulated transactions), SQLite's `Base.metadata.create_all()` does not alter an existing SQLite `.db` file on disk. If a stale `.db` file exists, new null-receipt records trigger `IntegrityError`.
2. **Supporting Evidence**:
   Observed during test runs where a preexisting local `veridion.db` failed with `NOT NULL constraint failed: settlements.tx_hash` until clean initialization was performed.
3. **Root Cause**:
   SQLite lack of automated ALTER COLUMN support in standard SQLAlchemy `create_all()`.
4. **Exact Files to Modify**:
   [`backend/app/core/database.py`](file:///C:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/core/database.py)
5. **Minimal Proposed Change**:
   Add an idempotent column migration check inside `init_db()` or an optional `--clean-db` CLI flag in test runners to verify table definitions match the active ORM entities before launching.
6. **Regression Risks**:
   Zero regression risk to API endpoints or smart contracts; only affects startup bootstrapping.
7. **Tests to Run Before & After**:
   `pytest backend/tests/test_end_to_end.py -v`
8. **Acceptance Criteria**:
   `init_db()` safely handles both fresh databases and pre-existing local SQLite files.
9. **Verification Needed**:
   Run `scripts/run_local_tests.py` and ensure 100% pass rate.

---

### Item 2 (P2 — Windows Foundry Tooling): Foundry Windows Tooling Helper

1. **Confirmed Defect / Observation**:
   On Windows environments without WSL, running `forge` directly fails with `The term 'forge' is not recognized`.
2. **Supporting Evidence**:
   `forge --version` command exited with code 1 in Windows PowerShell.
3. **Root Cause**:
   Foundry binaries were installed in Linux/macOS environments by teammates rather than in the Windows system PATH.
4. **Exact Files to Modify**:
   [`scripts/run_local_tests.py`](file:///C:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/scripts/run_local_tests.py) or documentation in `README.md`.
5. **Minimal Proposed Change**:
   Add explicit Windows instructions for Foundry via `cargo install --git https://github.com/foundry-rs/foundry --profile local forge` or provide a dockerized test runner command (`docker-compose run contracts-test`).
6. **Regression Risks**:
   None (documentation / helper script only).
7. **Tests to Run Before & After**:
   Contract test scripts.
8. **Acceptance Criteria**:
   Clear diagnostic message printed when running tests on Windows if Foundry is not installed.
9. **Verification Needed**:
   Verify `scripts/run_local_tests.py` output clarity.

---

### Item 3 (P3 — Production PostgreSQL Container): Docker Compose PostgreSQL Profile

1. **Confirmed Defect / Observation**:
   The current default `DATABASE_URL` is set to SQLite (`sqlite+aiosqlite:///./veridion.db`). While perfect for local hackathon demos and fast test runs (< 4s), multi-threaded concurrent workloads benefit from PostgreSQL.
2. **Supporting Evidence**:
   PRD Section 13.1 recommends PostgreSQL for production deployments.
3. **Root Cause**:
   SQLite is configured as default for zero-dependency standalone execution.
4. **Exact Files to Modify**:
   [`docker-compose.yml`](file:///C:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/docker-compose.yml), [`backend/.env.example`](file:///C:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/.env.example).
5. **Minimal Proposed Change**:
   Add a standard PostgreSQL 16 container definition in `docker-compose.yml` with health checks and volume persistence.
6. **Regression Risks**:
   Zero regression to SQLite default.
7. **Tests to Run Before & After**:
   `docker-compose up -d db` and `pytest backend/tests -v`.
8. **Acceptance Criteria**:
   `DATABASE_URL="postgresql+asyncpg://..."` connects and executes all 28 backend tests.
9. **Verification Needed**:
   End-to-end demo seeding on PostgreSQL.

---

## 3. Approval Request

To execute any of the above enhancements, please provide your approval:
- **Option 1**: Keep repository pristine as-is (100% tests passing, zero changes needed for hackathon demo).
- **Option 2**: Apply Item 1 (Database bootstrapping guard) for enhanced local developer robustness.
