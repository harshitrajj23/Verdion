# Phase 5C — Forecast Resolution, Scoring Determinism, and Settlement Integrity

## Overview

Regulatory forecasts in VERIDION must not be unvalidated subjective impressions. Predictions must be evaluated using strictly proper mathematical scoring rules where the unique incentive-compatible strategy is truthful reporting.

Furthermore, resolution criteria and sources must be declared *before* commitments are accepted, and settlement must be protected against unauthorized calls, double-payouts, and premature execution.

---

## 1. Strictly Proper Scoring Rules

Implemented in `backend/app/services/forecast_evaluator.py`:

### A. Multi-Outcome Brier Score
For a market with $K$ possible outcomes and forecaster probability distribution $p \in [0, 1]^K$, where $o_k \in \{0, 1\}$ is the actual indicator of outcome $k$:

$$\text{Brier} = \sum_{k=1}^K (p_k - o_k)^2$$

- For binary forecasts ($K=2$), if probability of YES is $p$ and actual outcome is $1$:
  $$\text{Brier} = (p - 1)^2 + ((1-p) - 0)^2 = 2(1-p)^2$$
- A lower Brier score indicates superior accuracy:
  - Perfect forecast ($p=1.0$, outcome YES): $\text{Brier} = 0.000000$
  - Complete error ($p=0.0$, outcome YES): $\text{Brier} = 2.000000$
  - Maximum uncertainty ($p=0.50$): $\text{Brier} = 0.500000$

### B. Binary Logarithmic Loss (Log Loss)
With probability clipping $[\epsilon, 1-\epsilon]$ where $\epsilon = 10^{-6}$ to prevent infinite penalties:

$$\text{LogLoss} = -\Big(y \ln(p) + (1-y)\ln(1-p)\Big)$$

---

## 2. Pre-Declared Resolution Criteria & Process

Every forecast market schema (`ForecastMarketRecord`) requires:
1. `proposition`: Unambiguous factual or legal condition (e.g., "Will the Irish DPC issue a fine against Meta regarding EU-US data transfers exceeding €100M before July 2026?").
2. `resolution_criteria`: Specific documentary or legal standard required to trigger an affirmative outcome.
3. `resolution_source`: Authoritative official registry (e.g., EDPB Sanction Register, CJEU Official Journal, Curia Press Release).
4. `closing_time`: Explicit cutoff date and time after which no further predictions are accepted.

### Prohibition on Autonomous Hallucinated Resolution
The system strictly forbids autonomous LLM agents from settling markets on the basis of model inference alone. An outcome can only be resolved by:
- An authorized evaluator whose cryptographic address matches `settings.EVALUATOR_ADDRESS`.
- Direct cryptographic oracle feed signed by an attested provider.
- Formal administrative appeal / dispute process.

---

## 3. Settlement State Machine & Anti-Tamper Safeguards

The settlement subsystem enforces atomic, one-way state transitions:

```
[OPEN] ---> [CLOSED] ---> [REVEAL_WINDOW] ---> [RESOLVED] ---> [SETTLED]
```

- **Premature Settlement Rejection:** Calling settlement before resolution raises `MarketSettlementException("Market is not in RESOLVED status")`.
- **Double Settlement Rejection:** Calling settlement on a market with status `SETTLED` raises `MarketSettlementException("Market already settled")`.
- **Unauthorized Evaluator Rejection:** Resolution requests with a caller address different from the designated evaluator are rejected with HTTP 403 / `UnauthorizedResolutionException`.
- **Credit Separation:** Local credits in simulated test accounts are recorded as `LOCAL_CREDITS_SIMULATED` and explicitly distinguished from ERC-20 token transfers or native ETH payouts.
