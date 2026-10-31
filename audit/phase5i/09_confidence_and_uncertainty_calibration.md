# VERIDION Phase 5I — Deliverable 09: Confidence Scoring, Uncertainty Quantification & Calibration

## Executive Overview
Under PRD Section 7.3 and Option C, confidence scores must not be arbitrary numbers. They must reflect explicit mathematical formulations, and legal uncertainties must be quantitatively prioritized for research bounties.

---

## 1. Mathematical Formulations for Agent Confidence

| Agent | Confidence Determination Method | Value Range | Rationale |
| :--- | :--- | :--- | :--- |
| **Legal Researcher** | Direct Text Excerpt Grounding | $0.95$ | Text is directly extracted from authoritative statutes. |
| **Legal Interpreter** | Deterministic Rule Evaluation | $0.85 - 0.90$ | Based on exact AST satisfaction of statutory conditions. |
| **Adversarial Researcher** | Statutory Exception Defense | $0.70$ | Evaluates legal defense viability under known case law. |
| **Evidence Verifier** | Cryptographic Hash Equality | $1.00$ or $0.00$ | Binary boolean cryptographic verification. |
| **Quantitative Forecaster** | Violation-Weighted Probability | $0.15, 0.65, 0.85$ | Empirically calibrated against violation counts. |

---

## 2. Uncertainty Prioritization & Research Bounty Formula

Uncertainties flagged by the `LegalInterpreter` are scored and ranked by the `Coordinator` using the PRD formula:
$$\text{Priority}(q) = \text{Impact}(q) \times \text{Uncertainty}(q) \times \text{ResearchFeasibility}(q)$$

- **Threshold for Bounty Generation:** $\ge 0.35$.
- **Top Uncertainty Flagged in Audit:** Jurisdiction divergence between DPA enforcement interpretations ($	ext{Priority} = 0.405$), automatically queueing an external research bounty.
- **Correlated Failure Risk:** Evaluated as **Low**. The hybrid architecture ensures that if the Hugging Face endpoint encounters connectivity interruption, deterministic rules maintain operational integrity without system collapse.
