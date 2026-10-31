# VERIDION Phase 5K — Deliverable 04: Unified Confidence Contract Audit Across 6 Agents

## 1. Schema Standardization

All six autonomous agent roles emit the standardized `ConfidenceContract` schema:

- `raw_confidence` (float in $[0.0, 1.0]$)
- `calibrated_confidence` (float in $[0.0, 1.0]$)
- `confidence_type` (Enum: `RULE_DERIVED`, `MODEL_ESTIMATED`, `CRYPTOGRAPHIC_INTEGRITY`, `EMPIRICALLY_CALIBRATED`)
- `calibration_status` (`UNCALIBRATED`, `HEURISTIC_BOUNDED`, `EMPIRICALLY_CALIBRATED`)
- `uncertainty_score` (float in $[0.0, 1.0]$)
- `supporting_evidence_count` (int $\ge 0$)
- `contradicting_evidence_count` (int $\ge 0$)
- `inference_mode` (`DETERMINISTIC_RULES`, `LIVE_MODEL`, `OFFLINE_FALLBACK`)
- `model_identifier` (string)

## 2. Agent Assignments & Anti-Conflation Invariant

Agent historical reputation scores (from the Prediction Market / AgentRegistry) are **strictly separated** from per-inference confidence contracts:

| Agent Role | Confidence Type | Raw Score | Calibrated Score | Calibration Method |
| :--- | :--- | :---: | :---: | :--- |
| **Legal Researcher** | `RULE_DERIVED` | 0.95 | 0.95 | Curated gazette text match |
| **Legal Interpreter** | `RULE_DERIVED` | 0.90 | 0.90 | Deterministic AST fact-to-law evaluation |
| **Adversarial Researcher** | `MODEL_ESTIMATED` | 0.70 | 0.65 | Bounded statutory exception search |
| **Evidence Verifier** | `CRYPTOGRAPHIC_INTEGRITY` | 1.00 | 1.00 | SHA-256 Merkle passage digest match |
| **Quantitative Forecaster** | `EMPIRICALLY_CALIBRATED` | 0.85 | 0.85 | Calibrated risk heuristic on $N=200$ |
| **Coordinator Synthesis** | `RULE_DERIVED` | 0.85 | 0.85 | Dialectic argument graph synthesis |

Reputation conflation is eliminated.
