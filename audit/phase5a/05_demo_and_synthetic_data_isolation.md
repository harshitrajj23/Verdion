# VERIDION PHASE 5A — DEMO AND SYNTHETIC DATA ISOLATION REPORT

**Document ID:** `audit/phase5a/05_demo_and_synthetic_data_isolation.md`  
**Execution Timestamp:** 2026-10-27T08:30:00+05:30  
**Scope:** Test Leakage Prevention, Demo Mode Isolation, and Truthful Empty States  

---

## 1. Executive Summary

A critical requirement of Phase 5A is preventing test fixtures, synthetic benchmark scenarios, and demo seeds from contaminating real-user workflows or being misrepresented as live production activity.

Prior to Phase 5A, running integration tests (`test_end_to_end.py`) unintentionally persisted test records (`Idempotent Case Creation Test`, `Async Job Test Case`) into `veridion.db`. Furthermore, the frontend client initialized by loading mock objects from `mockData.ts` if backend data was absent.

This report documents the architectural barriers implemented to guarantee complete isolation.

---

## 2. Test Fixture Leakage Remediation

### 2.1 The Hazard
In `backend/tests/test_end_to_end.py`, HTTP requests made via `httpx.AsyncClient` against `app` resolved database sessions through `backend/app/core/database.py:get_db()`, which binds directly to `settings.DATABASE_URL` (`sqlite+aiosqlite:///./veridion.db`). Consequently, every test run added rows to the operational SQLite database.

### 2.2 The Fix
An autouse fixture `isolated_test_env` was introduced in [`backend/tests/test_end_to_end.py`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/tests/test_end_to_end.py):
1. Creates an isolated in-memory SQLite database: `sqlite+aiosqlite:///:memory:`.
2. Overrides FastAPI dependency: `app.dependency_overrides[get_db] = override_get_db`.
3. Pre-initializes tables, corpus, and agents in memory.
4. Executes tests without touching `veridion.db`.
5. Clears overrides upon test completion (`app.dependency_overrides.clear()`).

**Empirical Proof:** Executing the entire 105-test backend suite resulted in **zero** new rows added to `veridion.db` (count remained constant at 69 cases).

---

## 3. Explicit Provenance Tagging & Filtering

### 3.1 Database Migration
The `cases` table was updated via a safe, non-destructive migration (`ALTER TABLE cases ADD COLUMN provenance VARCHAR(32) DEFAULT 'OPERATIONAL';`):
- `DEMO`: 41 cases created via `/api/v1/demo/seed`.
- `TEST`: 26 cases created during historical test suite runs.
- `OPERATIONAL`: 2 cases created during formal Phase 3/4 E2E protocol verification.

### 3.2 API Layer Isolation
`GET /api/v1/cases` was updated in [`backend/app/api/v1/cases.py`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/api/v1/cases.py) with query parameters:
- `exclude_test: bool = True` (defaults to excluding `TEST` cases).
- `provenance: Optional[str] = None` (allows explicit filtering, e.g. `provenance=OPERATIONAL`).

---

## 4. Frontend Truthfulness & Empty State Handling

### 4.1 Honest Empty State
In `frontend/src/lib/store.tsx`:
- Removed automatic fallback to `initialCase`, `initialMarkets`, and `initialBounties` when the backend returns valid empty responses (`[]`).
- If no cases exist in the database, `casesList` is set to `[]`, allowing UI components (`EmptyState.tsx`) to prompt the user to create their first genuine case.

### 4.2 Deceptive Offline Catch Block Removal
- Deleted all client catch blocks in `commitForecast`, `revealForecast`, `submitBountyEvidence`, `settleMarket`, and `settleBounty` that previously manufactured fake `"CONFIRMED"` statuses and fabricated pseudo-random transaction hashes.
- Actions now truthfully record `"REVERTED"` on failure and surface the actual network error.

---

## 5. Verification Verdict

**Status: PASS**. Test fixtures are strictly isolated to in-memory databases, demo data is explicitly tagged in the schema, and real-user mode presents honest empty states without deceptive mock fallbacks.
