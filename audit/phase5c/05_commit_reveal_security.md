# Phase 5C — Commit-Reveal Cryptographic Security & Verification Matrix

## Overview

In regulatory prediction markets and expert consensus forecasting, forecasters must not be able to observe peer predictions or real-world early signals before submitting their own positions. Without cryptographic commit-reveal guarantees, later participants can front-run predictions or claim post-hoc that they predicted an outcome.

Option C implements a **Two-Phase Commit-Reveal Scheme** enforcing pre-outcome binding and post-closure verification.

---

## 1. Cryptographic Binding Scheme

The commitment binds the market identifier, chosen outcome, and a 256-bit secret nonce:

$$\text{CommitmentHash} = \text{keccak256}\Big(\text{abi.encodePacked}(\text{market\_id}, \text{outcome}, \text{nonce})\Big)$$

### Encoding & Replay Prevention
- **Canonical Encoding:** The `market_id` string is strictly bound into the pre-image. This prevents **cross-forecast replay attacks** where a forecaster attempts to copy a valid commitment hash from Market A into Market B.
- **Nonce Entropy:** Nonces are generated using `secrets.token_hex(32)` (256 bits of cryptographic entropy). Nonce values must remain strictly confidential off-chain until the trading window is closed.
- **Outcome Normalization:** Outcomes are normalized strings (`YES`, `NO`, or categorical outcome names) validated against the market's permitted outcome set.

---

## 2. Protocol Timing Windows

```
   Market Open               Trading Closes             Reveal Closes            Resolution
        |                          |                          |                      |
        |====== COMMIT PHASE ======|====== REVEAL PHASE ======|=== RESOLUTION PHASE =|
        |                          |                          |                      |
   Submit Hash               Forecasters Reveal         Unrevealed Defaults     Authorized
   No Reveals                Nonce & Prediction         Commitments Voided      Evaluator
```

1. **Commit Window $[T_{\text{open}}, T_{\text{close}}]$:** Forecasters register commitments containing only `commitment_hash`. Reveals are rejected with `MarketCommitmentException`.
2. **Reveal Window $[T_{\text{close}}, T_{\text{reveal\_deadline}}]$:** Trading is halted. Forecasters submit `(outcome, nonce)`. The engine verifies `keccak256(...) == commitment_hash`.
3. **Resolution Window $[T > T_{\text{reveal\_deadline}}]$:** Any commitment left unrevealed is marked `VOID` / `UNREVEALED` and forfeits scoring. The authorized evaluator submits the ground truth outcome.

---

## 3. Comprehensive Attack Test Matrix

The commit-reveal implementation in `backend/app/services/market_service.py` was validated against all attack vectors in `backend/tests/test_phase5c_option_c.py`:

| Test Case | Scenario / Attack Vector | Expected Result | Actual Test Result |
| :---: | :--- | :--- | :--- |
| **01** | Correct reveal matching original outcome and nonce | Verification succeeds; status `REVEALED` | **PASS** |
| **02** | Incorrect reveal (different outcome submitted) | Hash mismatch; rejected | **PASS** |
| **03** | Modified prediction (attempted post-hoc shift) | Hash mismatch; rejected | **PASS** |
| **04** | Modified nonce (1-bit flipped or brute-forced) | Hash mismatch; rejected | **PASS** |
| **05** | Wrong forecast identifier (cross-market replay) | Hash mismatch; rejected | **PASS** |
| **06** | Duplicate reveal (replay of revealed transaction) | Rejected (`ALREADY_REVEALED`) | **PASS** |
| **07** | Reveal before trading deadline ($t < T_{\text{close}}$) | Rejected (`MARKET_STILL_OPEN`) | **PASS** |
| **08** | Reveal after deadline ($t > T_{\text{reveal\_deadline}}$) | Rejected (`REVEAL_WINDOW_EXPIRED`) | **PASS** |
| **09** | Unrevealed commitment at resolution time | Forfeited; excluded from payoff/settlement | **PASS** |
| **10** | Invalid or ambiguous outcome submission | Rejected (`INVALID_OUTCOME`) | **PASS** |
| **11** | Settlement attempted before resolution | Rejected (`MARKET_NOT_RESOLVED`) | **PASS** |
| **12** | Repeated settlement (double-spend/double-payout) | Rejected (`ALREADY_SETTLED`) | **PASS** |
| **13** | Unauthorized resolution (non-evaluator caller) | Rejected (`UNAUTHORIZED_RESOLUTION`) | **PASS** |

---

## 4. On-Chain vs. Off-Chain Verification

- **Off-Chain Verification:** Python implementation in `AuditVerifier` calculates `eth_hash.keccak256` or equivalent standard Keccak-256 libraries.
- **On-Chain Verification:** The `PredictionMarket.sol` contract contains `commitPrediction(bytes32 commitHash)` and `revealPrediction(string outcome, bytes32 nonce)` executing native EVM `keccak256(abi.encodePacked(...))`.
- **Zero Secret Leakage:** The audit packages and public APIs do **not** publish nonces until after the commitment is revealed. Tests confirm that unrevealed commitments in exported packages contain null/empty nonces.
