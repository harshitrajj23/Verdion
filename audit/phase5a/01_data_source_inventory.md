# VERIDION PHASE 5A — DATA SOURCE INVENTORY REPORT

**Document ID:** `audit/phase5a/01_data_source_inventory.md`  
**Execution Timestamp:** 2026-10-27T08:15:00+05:30  
**Audit Scope:** Full Database (`veridion.db`), API Endpoints, Frontend Store, Seeds, Benchmark Datasets, and Model Fallbacks  

---

## 1. Executive Summary

Phase 5A establishes forensic ground truth regarding every piece of data currently ingested, persisted, processed, or displayed in VERIDION. The objective is to determine what is genuine, externally sourced, user-generated, deterministically derived, simulated, synthetic, seeded, hardcoded, or unknown.

This forensic inventory audits all 16 relational database tables, seed scripts, benchmark fixtures, frontend initial states, and client simulation behaviors.

---

## 2. Complete Data Source Inventory Matrix

| Data Layer / Component | File / Location | Creation Mechanism | Data Classification | Independent Verification Status | Deception / Mock Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cases (`cases`)** | `backend/app/models/entities.py` | REST `POST /cases` or `POST /demo/seed` or Pytest runs | Mixed: 41 `DEMO_SEEDED`, 26 `TEST_FIXTURE_LEAKAGE`, 2 `OPERATIONAL_E2E_VERIFICATION` | Verified origins via SQLite created_at and request payloads | High prior risk: Test runs previously leaked into operational DB. |
| **Prediction Markets (`prediction_markets`)** | `backend/app/models/entities.py` | `POST /markets` or `POST /demo/seed` | 41 `DEMO_SEEDED`, 2 `OPERATIONAL_E2E_VERIFICATION` | Linked to parent case; local credit simulation | High prior risk: Presented identical synthetic outcomes (0.6333). |
| **Forecast Commitments (`forecasts`)** | `backend/app/models/entities.py` | `POST /markets/{id}/commit` & `reveal` | 123 `DEMO_SEEDED`, 2 `OPERATIONAL_E2E_VERIFICATION` | SHA-256 / Keccak-256 commitments verified | Medium: Demo forecasts used synthetic digest seeds (`0xaaaa...`). |
| **Evidence Bounties (`evidence_bounties`)** | `backend/app/models/entities.py` | `POST /bounties` or `POST /demo/seed` | 41 `DEMO_SEEDED`, 1 `OPERATIONAL_E2E_VERIFICATION` | Local simulated credit ledger (100 credits) | Medium: Simulated reward disbursements. |
| **Evidence Submissions (`bounty_submissions`)** | `backend/app/models/entities.py` | `POST /bounties/{id}/submissions` | 41 `DEMO_SEEDED`, 1 `OPERATIONAL_E2E_VERIFICATION` | Carries cryptographic passage digests | Low: Real legal quotes used in demo submissions. |
| **Settlements (`settlements`)** | `backend/app/models/entities.py` | `POST /markets/{id}/settle` or `POST /bounties/{id}/settle` | 166 records (`DEMO_SEEDED` & `OPERATIONAL`) | Local credit settlements | High prior risk: Previously simulated on-chain links in UI. |
| **Source Documents (`source_documents`)** | `ml/corpus/` & `retrieval_service.py` | Bundled primary legal text parsed on init | `OFFICIAL_LEGAL_SOURCE_FIXTURE` | Genuine text of GDPR (2016/679), AI Act, CCPA | Low: Verbatim statutory text; verified SHA-256 digests. |
| **Evidence Passages (`evidence_passages`)** | `backend/app/models/entities.py` | Segmented from source documents on init | `OFFICIAL_LEGAL_SOURCE_FIXTURE` | Bounded clause segmentation; SHA-256 digests | Verified: Digest matches normalized text. |
| **Protocol Agents (`agents`)** | `backend/app/models/entities.py` | `AgentService.initialize_agents` | `SYSTEM_REGISTERED_ROLE` | Fixed 6 core swarm roles with dedicated test addresses | Low: Static protocol configuration. |
| **Audit Events (`audit_events`)** | `backend/app/models/entities.py` | Append-only event logging in `AuditService` | 700 immutable audit entries | Cryptographic SHA-256 payload digests verified | Verified: Strict append-only hash chain. |
| **Transaction Records (`transaction_records`)** | `backend/app/models/entities.py` | `BlockchainService.record_simulated_transaction` | Currently 0 records | Local ledger tracking table | Clean: No false on-chain receipts logged here. |
| **Benchmark Scenarios** | `ml/benchmark/data/` | 20 curated discrimination scenarios | `SYNTHETIC_BENCHMARK_FIXTURE` | Verifiable discrimination dataset with frozen answers | Valid: Isolated to benchmark evaluation. |
| **Frontend Initial Mock State** | `frontend/src/lib/mockData.ts` | Hardcoded TypeScript objects (`initialCase`, etc.) | `SYNTHETIC_CLIENT_MOCK` | Curated sample presentation | High prior risk: UI displayed sample if DB was empty. |
| **Frontend Random Hashes** | `frontend/src/lib/store.tsx` | `generateTxHash()` math.random generator | `FABRICATED_PSEUDO_HASH` | Invalid; fabricated client hex strings | Remediation: Replaced with explicit `sim_tx_*` identifiers. |
| **Frontend Silent Fallbacks** | `frontend/src/lib/store.tsx` | Offline catch blocks faking "CONFIRMED" | `FABRICATED_OFFLINE_SUCCESS` | Fraudulent simulation of backend success | Remediation: Eliminated; throws real error. |

---

## 3. Findings & Vulnerabilities Discovered

1. **Test Leakage into Production Database:**
   - Prior to Phase 5A, executing `backend/tests/test_end_to_end.py` operated directly against `veridion.db` without dependency overrides, leaking 26 test cases (`Idempotent Case Creation Test`, `Async Job Test Case`) into the persisted store.
2. **Deceptive Offline Fallback in Client Store:**
   - In `frontend/src/lib/store.tsx`, when backend endpoints failed, `catch` blocks silently waited 1000ms, generated a random 64-character hex string, updated the transaction status to `"CONFIRMED"`, and falsely notified the user that the action succeeded offline.
3. **Frontend Initial State Obfuscating Empty Databases:**
   - In `store.tsx`, if the database returned an empty array of cases or markets, the UI retained `initialCase` and `initialMarkets` from `mockData.ts`, hiding the fact that the system had zero real data.
4. **Duplicate Demo Seeding:**
   - 41 identical cases of `"AI-Powered Customer Support Analytics"` were accumulated in `veridion.db` from repeated automated calls to `/api/v1/demo/seed`.

---

## 4. Verification Verdict

All data sources have been cataloged with exact origins, file locations, and verification statuses. Remediation measures have been designed to isolate test fixtures, enforce honest empty states, and eliminate silent client mock fallbacks.
