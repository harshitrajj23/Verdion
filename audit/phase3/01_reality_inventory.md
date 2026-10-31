# VERIDION PHASE 3 — REALITY INVENTORY REPORT
**Document Reference:** `audit/phase3/01_reality_inventory.md`  
**Evaluation Standard:** PRD v1.0, Sections 1–18  
**Timestamp:** 2026-10-27T06:40:00Z  
**Branch:** `Divyank` | **Commit Baseline:** `ca33ac2`

---

## 1. Executive Summary

This inventory documents every instance of simulated, precomputed, hardcoded, or mock behavior discovered across the VERIDION codebase. In accordance with Phase 3 Reality Engineering requirements, each occurrence was discovered via targeted regex/AST scans, inspected, and classified into one of seven definitive categories:

1. **Legitimate Constant:** Mathematical, protocol, architectural, or regulatory constants (e.g., chain IDs, SHA-256 genesis digests, mathematical formulas, default agent roles).
2. **Test Fixture:** Synthetic datasets, mocks, and isolated testing harnesses used strictly inside `tests/` directories or unit test suites.
3. **Explicit Demo Functionality:** Deliberate demonstration capabilities (e.g., `/api/v1/demo/seed`, Appendix A demonstration walkthrough) that are visibly demarcated and isolated.
4. **Non-Production Fallback:** Graceful degradation code (e.g., when external Hugging Face inference is offline, falling back to deterministic legal rule execution with transparent logging).
5. **Unimplemented Feature:** Inert UI elements or stubbed endpoints that advertised capability without performing actions.
6. **Misleading Mock Behavior:** Hardcoded fake returns, artificial latency, or in-memory state updates masquerading as persistent backend execution or on-chain transaction receipts.
7. **Security or Data-Integrity Defect:** Flaws causing data loss, lazy loading crashes, or unvalidated state transitions.

---

## 2. Inventory Classification Summary

| Category | Discovered Count | Remediated in Phase 3 | Retained Legitimate | Unresolved Blockers |
| :--- | :---: | :---: | :---: | :---: |
| **Misleading Mock Behavior** | 12 | 12 | 0 | 0 |
| **Security / Data Integrity Defect** | 2 | 2 | 0 | 0 |
| **Unimplemented Feature** | 3 | 3 | 0 | 0 |
| **Non-Production Fallback** | 4 | 4 (Disclosed) | 0 | 0 |
| **Explicit Demo Functionality** | 3 | 0 | 3 (Demarcated) | 0 |
| **Test Fixtures** | 24 | 0 | 24 (Isolated) | 0 |
| **Legitimate Constants** | 65 | 0 | 65 (Documented) | 0 |
| **TOTAL** | **113** | **21** | **92** | **0** |

---

## 3. High-Risk Findings and Remediations

### 3.1. Frontend-Only State Mutations Masquerading as Protocol Persistence
- **Location:** `frontend/src/lib/store.tsx` (Lines 184–447)
- **Defect:** Actions (`commitForecast`, `revealForecast`, `submitBountyEvidence`, `settleMarket`, `settleBounty`) generated pseudo-random hex strings via client-side `generateTxHash()`, added synthetic latency via `setTimeout`, and mutated only local React state. Toast notifications claimed "Confirmed on Testnet".
- **Risk:** High. A page refresh discarded all forecasts, bounties, and settlements.
- **Phase 3 Remediation:** Engineered `frontend/src/lib/api.ts` and wired `StoreProvider` directly to FastAPI backend (`/api/v1/...`) via Next.js proxy rewrites. All state mutations now execute real persistent backend operations and survive reloads.

### 3.2. MissingGreenlet Response Serialization Crashes
- **Location:** `backend/app/models/entities.py` (Lines 166, 207)
- **Defect:** `PredictionMarket.forecasts` and `EvidenceBounty.submissions` relationships used default lazy loading. Under FastAPI async execution with `aiosqlite`, querying `/api/v1/markets` or `/api/v1/bounties` triggered `MissingGreenlet` internal server errors.
- **Risk:** Critical. Prevented frontend from querying stored markets and bounties.
- **Phase 3 Remediation:** Configured `lazy="selectin"` on both relationships. Both endpoints now return full structured arrays with eager loading and zero greenlet errors.

### 3.3. Artificial Delays and Fixed Metric Scores in Evaluation
- **Location:** `backend/app/services/evaluation_service.py` (Lines 54, 62, 96, 104, 156, 164)
- **Defect:** Artificial padding (`+ 120.0`, `+ 340.0`, `+ 480.0` ms) added to execution time; hardcoded citation validities (`0.72`, `0.88`, `0.98`) and unsupported claim rates (`0.28`, `0.12`, `0.02`) returned as benchmark averages.
- **Risk:** High. Masked actual evaluation performance and presented fabricated telemetry.
- **Phase 3 Remediation:** Replaced artificial padding with wall-clock execution timing. Dynamically calculated citation validity and unsupported claim rates from actual statutory matches and passage verification outputs.

### 3.4. Hardcoded Dashboard Brier Score and Static Entity Counts
- **Location:** `frontend/src/app/page.tsx` (Lines 122, 133–158)
- **Defect:** Dashboard hardcoded `Active Cases: 1`, `Prediction Markets: 1 Reveal, 1 Settled`, `Brier Score: 0.0210`, and `Settlements: 1` as static JSX strings.
- **Risk:** Moderate. Made dashboard appear frozen and disconnected from actual activity.
- **Phase 3 Remediation:** Rewrote metric cards to dynamically compute values from live state: `casesList.length`, active/settled market counts, and real mean Brier score over revealed forecasts (displaying `—` with `Awaiting Settlement` when no settled forecasts exist).

### 3.5. Inert Case Creation and Analysis Controls
- **Location:** `frontend/src/app/cases/page.tsx`
- **Defect:** No UI controls existed for creating a new case or triggering swarm analysis.
- **Risk:** Moderate. Prevented users from exercising real end-to-end case workflows from the browser.
- **Phase 3 Remediation:** Implemented an accessible "New Case" modal with validated fields (title, question, jurisdiction, data categories, processing purpose) and a "Run Swarm Analysis" button that triggers `POST /cases/{id}/analyze?sync=true` with live execution feedback.
