# VERIDION Phase 5K — Deliverable 07: Compact 28-Attack Adversarial Regression Results

## 1. Summary

- **Total Attacks Executed:** 28
- **Total Attacks Defended / Rejected:** 28
- **Defense Success Rate:** **100.0%**

## 2. Complete Attack Register

| Attack # | Category | Attack Description | Defended | Defense Mechanism / Audit Finding |
| :---: | :--- | :--- | :---: | :--- |
| 01 | `EVIDENCE` | Modified passage text (digest mismatch) | **YES** | Passage integrity check failed closed. |
| 02 | `EVIDENCE` | Invalid citation reference format | **YES** | Non-statutory citation syntax rejected. |
| 03 | `EVIDENCE` | Unsupported synthetic claim (hallucination) | **YES** | Zero lexical/semantic overlap rejected. |
| 04 | `EVIDENCE` | Stale / future repealed authority (temporal mismatch) | **YES** | Authority effective after assessment date rejected. |
| 05 | `EVIDENCE` | Extra-jurisdictional legal authority | **YES** | California authority applied to EU case rejected. |
| 06 | `EVIDENCE` | Fabricated direct quotation marks | **YES** | Quotation accuracy contradiction rejected. |
| 07 | `EVIDENCE` | Unauthenticated source document | **YES** | Unverified provenance rejected. |
| 08 | `EVIDENCE` | Invalid deontic legal entailment | **YES** | Deontic ambiguity flagged for human review. |
| 09 | `AGENT` | Model provider timeout / offline handling | **YES** | Handled safely via deterministic offline fallback. |
| 10 | `AGENT` | Provider rate limit HTTP 429 | **YES** | Recovered gracefully without uncaught exception. |
| 11 | `AGENT` | Malformed JSON from provider | **YES** | Captured raw text without crashing parser. |
| 12 | `AGENT` | Offline fallback safety under network outage | **YES** | Clean fallback mode enabled. |
| 13 | `AGENT` | Direct agent contradiction handling | **YES** | Disagreement identified and recorded (0.30 delta). |
| 14 | `AGENT` | Duplicate evidence injection (citation stuffing) | **YES** | Duplicate passage deduplicated cleanly. |
| 15 | `AGENT` | Prompt injection in case facts | **YES** | Deterministic rule analysis ignored prompt injection payload and detected violation. |
| 16 | `AGENT` | Out-of-bounds agent confidence score (>1.0) | **YES** | Pydantic validator rejected score > 1.0. |
| 17 | `FORECAST` | Forecast probability < 0.0 | **YES** | Negative probability rejected. |
| 18 | `FORECAST` | Forecast probability > 1.0 | **YES** | Probability > 1.0 rejected. |
| 19 | `FORECAST` | Missing ground truth label at settlement | **YES** | Empty ground truth set rejected. |
| 20 | `FORECAST` | Split data leakage between DEV and TEST | **YES** | 0 shared scenario IDs confirmed. |
| 21 | `COMMITMENT` | Commitment reveal with altered chain ID | **YES** | Reconstructed hash mismatch rejected. |
| 22 | `COMMITMENT` | Commitment reveal with altered market ID | **YES** | Market ID mismatch rejected. |
| 23 | `COMMITMENT` | Commitment reveal with altered agent address | **YES** | Caller address mismatch rejected. |
| 24 | `COMMITMENT` | Commitment reveal with altered probability | **YES** | Probability mismatch rejected. |
| 25 | `COMMITMENT` | Commitment reveal with altered evidence digest | **YES** | Digest mismatch rejected. |
| 26 | `COMMITMENT` | Commitment reveal with altered nonce | **YES** | Nonce mismatch rejected. |
| 27 | `COMMITMENT` | Cross-market commitment replay attack | **YES** | Replay into different market ID rejected. |
| 28 | `COMMITMENT` | Malformed non-hex digest rejection | **YES** | Malformed non-hex digest rejected with ValueError. |
