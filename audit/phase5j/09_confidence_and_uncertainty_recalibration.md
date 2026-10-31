# VERIDION Phase 5J — Deliverable 09: Unified Confidence Architecture & Uncertainty Recalibration

## Executive Summary
This report documents the resolution of **Finding C**, detailing the unified `ConfidenceContract` schema implemented across all specialist agents.

---

## 1. Unified Authoritative Confidence Contract

All six agents now emit standardized `ConfidenceContract` objects with explicitly typed confidence:

| Agent Name | Raw Confidence | Confidence Type | Calibration Status | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Legal Researcher** | 0.95 | `RULE_DERIVED` | `HEURISTIC_BOUNDED` | Direct gazette textual quotation |
| **Legal Interpreter** | 0.9 | `RULE_DERIVED` | `HEURISTIC_BOUNDED` | Deterministic AST condition evaluation |
| **Adversarial Researcher** | 0.7 | `MODEL_ESTIMATED` | `UNCALIBRATED` | Model counterargument or statutory defense |
| **Evidence Verifier** | 1.0 | `CRYPTOGRAPHIC_INTEGRITY` | `EMPIRICALLY_CALIBRATED` | SHA-256 equality and 9-dim grounding check |
| **Quantitative Forecaster** | 0.85 | `EMPIRICALLY_CALIBRATED` | `EMPIRICALLY_CALIBRATED` | Calibrated risk heuristic on synthetic corpus |
| **Coordinator** | 0.85 | `RULE_DERIVED` | `HEURISTIC_BOUNDED` | Graph synthesis & priority scoring |

---

## 2. Uncertainty Prioritization Formula
The Coordinator ranks legal ambiguities using the formula:
$$\text{Priority}(q) = \text{Impact}(q) \times \text{Uncertainty}(q) \times \text{ResearchFeasibility}(q)$$
Bounties are automatically triggered for unresolved questions with $\text{Priority} \ge 0.35$.
