# VERIDION Phase 5J — Deliverable 06: Independent Legal Benchmark Methodology & Dataset Design

## Executive Summary
This document establishes the methodology for the new **100-scenario independent benchmark dataset** (`backend/data/benchmark_100_scenarios.json`), replacing reliance on the legacy 20-scenario dataset.

---

## 1. Dataset Architecture & Stratification

| Stratification Split | Scenario Count | Purpose |
| :--- | :--- | :--- |
| **DEV Split** | 30 scenarios | Internal rule development and condition calibration |
| **VAL Split** | 30 scenarios | Hyperparameter and confidence threshold tuning |
| **TEST Split** | 40 scenarios | Strictly held-out test evaluation without developer contamination |
| **Total Scenarios** | **100 scenarios** | Comprehensive multi-jurisdictional evaluation |

---

## 2. Legal Domains & Instruments Covered
- **EU General Data Protection Regulation (GDPR):** Articles 5(1)(b), 5(1)(e), 6(1)(a), 9(1), 13, 17, 22, 28, 44.
- **EU Artificial Intelligence Act (AI Act):** Article 50 (transparency obligations for synthetic audio/avatars).
- **California Consumer Privacy Act (CCPA/CPRA):** Cal. Civ. Code §§ 1798.100, 1798.120 (opt-out of sale/sharing).
- **Industry Sectors:** Fintech, Healthcare, E-Commerce, Telecom, Automotive, Gaming, EdTech, Recruiting, Hospitality, Logistics.
