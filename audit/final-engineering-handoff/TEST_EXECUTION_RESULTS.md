# VERIDION — Test Execution & Verification Results

## 1. Automated Test Suite Summary

- **Adversarial Regression Suite (28 Test Attacks):** 28 of 28 defended (100.0% defense rate).
  - 8 Evidence attacks: modified passage, bad citation, unsupported claim, stale law, wrong jurisdiction, fabricated quote, unverified source, invalid entailment. (All defended).
  - 8 Agent attacks: provider timeout, rate limit HTTP 429, malformed JSON, offline fallback, agent contradiction, citation stuffing, prompt injection, out-of-bounds confidence. (All defended).
  - 4 Forecast attacks: probability < 0, probability > 1, missing ground truth, split data leakage. (All defended).
  - 8 Commitment attacks: altered chain ID, altered market ID, altered agent address, altered probability, altered evidence digest, altered nonce, replay attack, non-hex malformed input. (All defended).
- **Crypto & Commit-Reveal Suite (`test_crypto.py`):** 9 passed in 0.91s.
- **Frontend Compilation & Production Build:** `npx tsc --noEmit` exited code 0; `npm run build` compiled all 13 routes successfully.
- **End-to-End Decision Workflow:** 10 stages executed in 0.28 ms with Merkle root bitwise identity verified.
