# VERIDION PHASE 5E AUDIT REPORT — ARTIFACT 05
# Resolution Criteria, Scoring, & Operational Metric Segregation

**Document Reference:** `VERIDION-AUDIT-P5E-005`  
**Phase:** 5E (Option C — Auditable Regulatory Decision Infrastructure)  
**Date of Verification:** 2026-10-28  
**Verification Lead:** Forecast Evaluator & QA Lead  
**Resolution & Scoring Status:** **VERIFIED (Strict Metric Segregation Enforced)**

---

## 1. Resolution Framework

A legal opinion is not an assumption of truth; a regulatory forecast must bind to objective, verifiable resolution criteria declared *prior* to outcome knowledge.

### 1.1 Resolution Metadata Schema
```json
{
  "market_id": "market_cjeu_case_c252_21",
  "resolution_criteria": "CJEU judgment in Case C-252/21 published on official curia.europa.eu portal",
  "authoritative_source_url": "https://curia.europa.eu/juris/document/document.jsf?text=&docid=275217&pageIndex=0&doclang=EN&mode=req&dir=&occ=first&part=1&cid=123456",
  "resolution_criteria_version": "1.0.0",
  "resolution_timestamp": "2026-10-28T05:30:00Z",
  "outcome": 1,
  "adjudicator": "0xEvaluator",
  "supporting_citation": "CJEU Case C-252/21 Meta Platforms v Bundeskartellamt, paragraph 73",
  "dispute_status": "NONE"
}
```

If an official outcome source is unavailable or ambiguous, the market must remain in `RESOLUTION_PENDING` or transition to `DISPUTED`. It must never fabricate an operational resolution.

---

## 2. Independent Scoring Recalculation

For binary probability forecasts $p_i \in [0, 1]$ and actual binary outcome $y \in \{0, 1\}$, scoring is computed via the standard Brier Score and Quadratic Scoring Rule:

$$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^{N} (p_i - y)^2$$
$$\text{Quadratic Payoff} = 100 \cdot \big(1 - (p_i - y)^2\big)$$

In Phase 5E, the scoring engine in [`ForecastEvaluator`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/services/forecast_evaluator.py) was tested against independent calculations:
- Prediction $p = 0.85$, Outcome $y = 1 \implies \text{Score} = (0.85 - 1)^2 = 0.0225$ (Lower is better).
- Verified that duplicate settlements are rejected (`SettlementAlreadyDoneException`).

---

## 3. Metric Segregation (Scenario 6 & 7 Verification)

### 3.1 Scenario 6 — Unresolved Real Forecast Exclusion
In `test_scenario_06_unresolved_real_forecast_exclusion`, an operational market is open and active:
- It has not occurred yet.
- Outcome is `None`, status is `OPEN` / `RESOLUTION_PENDING`.
- **Audited Metric:** When computing overall operational accuracy, unresolved forecasts are strictly filtered out ($N=0$).
- **Reported Metric:** Operational Brier score: `None`, Sample size: `0`. No synthetic outcomes substitute for real outcomes.

### 3.2 Scenario 7 — Test-Only Resolution Segregation
In `test_scenario_07_test_only_resolution_metric_segregation`:
- A synthetic test market was resolved using `provenance="TEST"`.
- When querying operational metrics:
  ```python
  op_metrics = await ForecastEvaluator.get_operational_accuracy(test_db)
  assert op_metrics["sample_size"] == 0
  assert op_metrics["brier_score"] is None
  ```
- Test and demo resolutions can NEVER contaminate operational evaluation metrics.
