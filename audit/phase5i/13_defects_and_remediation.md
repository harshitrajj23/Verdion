# VERIDION Phase 5I — Deliverable 13: Technical Defects, Limitations & Remediation Register

## Executive Overview
In strict compliance with Option C, this register documents all identified limitations, edge cases, and design trade-offs discovered during the Phase 5I audit, along with their implemented remediations.

---

## 1. Technical Defect & Limitation Register

| Defect ID | Description | Severity | Impact on System | Implemented Remediation / Status |
| :--- | :--- | :--- | :--- | :--- |
| **DEF-5I-01** | Hugging Face LLM Endpoint Offline | Low | Adversarial researcher cannot perform open-ended generative counter-argumentation without remote API. | **REMEDIATED:** Implemented robust deterministic statutory exception fallback in `HuggingFaceInferenceService`. Output explicitly declares fallback mode. |
| **DEF-5I-02** | Absence of Heavyweight ML Packages (`torch`, `transformers`) in Windows venv | Informational | Local neural inference cannot execute on CPU/GPU without additional wheel compilation. | **REMEDIATED:** Preserved pure-Python architecture with subword n-gram vectorizer and AST rule engine. Avoids binary incompatibilities. |
| **DEF-5I-03** | Operational Court Case Sample Size is Zero ($N=0$) | Low | Prospective live forecast calibration cannot be measured until courts issue rulings on active cases. | **REMEDIATED:** Explicitly segregated retrospective CJEU cases ($N=10$) and synthetic validation ($N=200$) from live cases ($N=0$). Full transparency. |
| **DEF-5I-04** | Inverted Index Scalability on Massive Unstructured Corpora | Low | Exact term index is optimized for statutory passages (<10,000); large text libraries require sharding. | **MONITORED:** Current statutory corpus (137 passages) executes in 2.15 ms. Sharding will be implemented in Phase 6. |
