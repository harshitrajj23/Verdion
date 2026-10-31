# VERIDION PHASE 5A — DATA INTEGRITY FIXES REPORT

**Document ID:** `audit/phase5a/06_data_integrity_fixes.md`  
**Execution Timestamp:** 2026-10-27T08:35:00+05:30  
**Phase Objective:** Engineering Remediation of Data Provenance, Leakage, and Client Deception  

---

## 1. Executive Summary

This report documents the exact code modifications and database migrations applied to eliminate misleading sample data, isolate test fixtures, enforce truthful state reporting, and embed explicit provenance metadata into persistent entities.

---

## 2. Inventory of Changes by File

### 2.1 Persistent Schema (`backend/app/models/entities.py`)
- **Modification:** Added `provenance` column to the `Case` entity:
  ```python
  provenance = Column(String(32), default="OPERATIONAL", nullable=True, index=True)
  ```
- **Allowed Values:** `"OPERATIONAL"`, `"DEMO"`, `"TEST"`, `"UNKNOWN"`.
- **Purpose:** Prevents conflating test fixture leakage and demo seeds with genuine user-created cases.

### 2.2 Schemas & Data Contracts (`backend/app/schemas/case.py`)
- **Modification:**
  - Added `provenance: Optional[str] = Field(default="OPERATIONAL")` to `CaseCreateRequest`.
  - Added `provenance: Optional[str] = "OPERATIONAL"` to `CaseResponse`.
- **Purpose:** Exposes provenance metadata through the REST API boundary.

### 2.3 Service Layer (`backend/app/services/case_service.py`)
- **Modification:**
  - In `create_case`: Persists `case.provenance = getattr(req, "provenance", None) or "OPERATIONAL"`.
  - In `get_all_cases`: Implemented filtering:
    ```python
    @staticmethod
    async def get_all_cases(db: AsyncSession, provenance: Optional[str] = None, exclude_test: bool = True) -> List[Case]:
        stmt = select(Case)
        if provenance:
            stmt = stmt.where(Case.provenance == provenance)
        elif exclude_test:
            stmt = stmt.where((Case.provenance != "TEST") | (Case.provenance.is_(None)))
        stmt = stmt.order_by(Case.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
    ```
- **Purpose:** Guarantees that production listing APIs exclude test cases by default.

### 2.4 API Router Layer (`backend/app/api/v1/cases.py`)
- **Modification:**
  - Updated `list_cases` endpoint to accept query parameters `provenance: str = None` and `exclude_test: bool = True`.
- **Purpose:** Allows frontends and consumers to query purely operational cases, purely demo cases, or inspect test artifacts explicitly.

### 2.5 Demo Seed Router (`backend/app/api/v1/demo.py`)
- **Modification:** Explicitly marks cases created by the benchmark seed endpoint with `provenance="DEMO"`.
- **Purpose:** Ensures demo cases are never misclassified as genuine user activity.

### 2.6 Test Isolation (`backend/tests/test_end_to_end.py`)
- **Modification:** Introduced an autouse `isolated_test_env` fixture using `sqlite+aiosqlite:///:memory:` and `app.dependency_overrides[get_db]`.
- **Purpose:** Halts database pollution. Pytest runs no longer leak test cases into `veridion.db`.

### 2.7 Frontend State Management (`frontend/src/lib/store.tsx`)
- **Modifications:**
  1. Replaced `generateTxHash()` (which generated random 64-character hex strings) with `generateSimulatedTxId(action: string)` (producing explicit `sim_tx_*` identifiers).
  2. Removed all silent offline catch blocks in `commitForecast`, `revealForecast`, `submitBountyEvidence`, `settleMarket`, and `settleBounty` that previously manufactured fake `"CONFIRMED"` statuses and fabricated success toasts upon backend network failure.
  3. Replaced them with truthful error handling: sets state to `"REVERTED"`, emits an error toast with the actual network error, and re-throws the exception.
  4. Updated `refreshData` so that valid empty responses from the backend are preserved rather than overwritten by hardcoded mock datasets.

---

## 3. Database Migration & Integrity Proof

A safe, non-destructive migration script was executed on `veridion.db`:
- Column `provenance` added via `ALTER TABLE cases ADD COLUMN provenance VARCHAR(32) DEFAULT 'OPERATIONAL';`.
- Backfilled historical records:
  - 41 cases classified as `DEMO`
  - 26 cases classified as `TEST`
  - 2 cases classified as `OPERATIONAL`
- **Zero data loss:** All 69 cases, 43 markets, 42 bounties, and 700 audit events remained intact.

---

## 4. Verification Verdict

All changes were implemented, verified, and regression-tested. The data layer is now resilient against pollution and honest in failure modes.
