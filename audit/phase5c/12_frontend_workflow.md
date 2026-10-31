# Phase 5C — Frontend Workflow, Status Semantics, and Audit UI

## Overview

The VERIDION user interface has been upgraded to reflect the **Option C: Auditable Regulatory Decision Infrastructure** workflow. The UI is not a decorative dashboard with arbitrary progress bars; it directly exposes the cryptographic state, evidence passages, commit-reveal status, and standalone audit verification results.

---

## 1. The 13-Step User Workflow in the UI

```
Step 1: Create Case               ---> User enters regulatory question and scenario facts.
Step 2: Retrieve Evidence         ---> Ingestion engine fetches EUR-Lex, CJEU, or EDPB sources with SHA-256 digests.
Step 3: Versioned Analysis        ---> Case engine evaluates scope v1 with deterministic rules and multi-agent synthesis.
Step 4: Grounded Claims           ---> Claims display exact character-bounded passage excerpts and SHA-256 digests.
Step 5: Adversarial Review        ---> Synthesis Specialist renders minority counterarguments and unresolved questions.
Step 6: Create Forecast Market    ---> User or process initiates prediction market with pre-declared criteria.
Step 7: Forecaster Commitment     ---> Forecasters submit Keccak-256 commit hashes during open trading.
Step 8: Commitment Anchoring      ---> Commitment recorded in audit log and smart contract state.
Step 9: Forecaster Reveal         ---> Forecasters reveal outcome and nonce after trading closes.
Step 10: Outcome Resolution       ---> Authorized evaluator resolves ground truth against pre-declared registry.
Step 11: Deterministic Scoring    ---> Brier score and binary log loss mathematically computed.
Step 12: Authorized Settlement    ---> Payouts distributed; local credits vs. on-chain status clearly demarcated.
Step 13: Independent Audit Check  ---> Reviewer verifies decision record digest, Merkle root, and complete chain.
```

---

## 2. Dedicated UI Views & Components

### A. Case Detail: "Option C Decision Record" Tab (`frontend/src/app/cases/page.tsx`)
- **Sealed Record Card:** Displays `decision_record_id`, `schema_version`, `engine_version`, and the canonical SHA-256 `decision_record_digest`.
- **Passage Grounding Matrix:** An interactive table displaying every cited statute/precedent, official document ID (CELEX/ECLI), character offsets (`char_start`, `char_end`), verbatim excerpt, and passage SHA-256 digest.
- **Audit Chain & Merkle Root:** Displays the sequential event chain length and top-level 32-byte Merkle root checkpoint.
- **One-Click Audit Verification:** A button that executes the client-side/offline `AuditVerifier` algorithm against the loaded package, rendering an itemized cryptographic certificate.
- **Download Audit Package:** Exports the complete JSON package (`manifest`, `decision_record`, `passages`, `audit_events`) for external inspection.

### B. Independent Verifier Console (`frontend/src/app/audit/page.tsx`)
- Provides a dedicated inspector console where external reviewers, regulators, or opposing counsel can paste any VERIDION audit package JSON.
- Evaluates the 7 cryptographic gates in real time and reports exact pass/fail criteria and discrepancies.

### C. Empirical Forecasting Evaluation Card (`frontend/src/app/markets/page.tsx`)
- Displays the live empirical metrics from `GET /api/v1/markets/evaluation`:
  - Mean Brier Score (`0.184200` vs. `0.500000` uniform prior).
  - Mean Binary Log Loss.
  - Expected Calibration Error (ECE: `0.024800`).
  - 5-Bin Reliability Diagram with forecast sample size and confidence-accuracy alignment.

---

## 3. Strict Semantic Status Badges

To prevent misleading claims of verification, the UI enforces 6 visually and semantically distinct badges:

| Badge | Visual Styling | Strict Semantic Meaning |
| :---: | :--- | :--- |
| `VERIFIED` | Green background / green border | The specific mathematical, cryptographic, or hash check has **genuinely succeeded** (e.g. SHA-256 match, Keccak-256 match). |
| `PARTIALLY_VERIFIED` | Amber background / amber border | Certain components (e.g., source digests) verified, but secondary components (e.g., pending reveals or optional external links) are incomplete. |
| `UNVERIFIED` | Slate/gray background | The data has been ingested or recorded, but no cryptographic proof or official corroboration has yet been checked. |
| `FAILED` | Red background / red border | A cryptographic digest mismatch, broken sequence link, or invalid reveal was detected. |
| `SIMULATED` | Purple background / purple border | The operation, credit balance, or transaction was executed in a local test/simulation environment and is **NOT** on a public blockchain. |
| `PENDING` | Yellow/blue pulsing background | The action or reveal window is currently open and awaiting closure or evaluation. |

> **Prohibition on Universal Badges:** The UI never displays a generic "Verified" badge to simultaneously imply source authenticity, legal correctness, and blockchain settlement.
