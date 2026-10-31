# VERIDION Phase 5J — Deliverable 16: Updated Agent, ML & Grounding Architecture

## Executive Summary
This document provides the authoritative architectural blueprint for VERIDION following Phase 5J enhancements.

---

## 1. Updated Architectural Topology

```mermaid
flowchart TD
    subgraph Intake["1. Regulatory Intake & Evidence Binding"]
        Facts["Case Facts & Scope"] --> Ret["Retrieval Subsystem\n(Inverted Index + TF-IDF)"]
        Ret --> Passages["Passages with Digests"]
    end

    subgraph Analysis["2. Specialist Legal Analysis"]
        Passages --> LR["Legal Researcher\n(Statutory Extraction)"]
        LR --> StatClaims["Statutory Claims\n(ConfidenceContract: 0.95)"]
        StatClaims --> LI["Legal Interpreter\n(Deterministic AST Engine)"]
        Facts --> LI
        LI --> RiskClaims["Risk Claims\n(ConfidenceContract: 0.90)"]
    end

    subgraph Adversarial["3. Adversarial Stress-Testing"]
        RiskClaims --> AR["Adversarial Researcher\n(Provider Integration / Fallback)"]
        AR --> Defenses["Exception Claims & Objections\n(ConfidenceContract: 0.70)"]
    end

    subgraph Verification["4. Multi-Dimensional Grounding"]
        StatClaims & RiskClaims & Defenses --> EV["Evidence Verifier\n(EvidenceGroundingService)"]
        EV --> NineDim["9 Grounding Dimensions Evaluated\n(Integrity, Citation, Entailment)"]
        NineDim --> GroundedClaims["Verified Grounded Claims"]
    end

    subgraph Forecasting["5. Calibrated Forecasting & Commitment"]
        RiskClaims --> QF["Quantitative Forecaster\n(Calibrated Heuristic)"]
        QF --> Commit["6-Field Fixed-Width Commitment\n(keccak256 hash with 256-bit salt)"]
    end

    subgraph Synthesis["6. Argument Graph & Sealing"]
        GroundedClaims & Defenses & Commit --> Coord["Coordinator Agent\n(Argument Graph & Ranking)"]
        Coord --> Graph["Relational Graph\n(CONTRADICTS edges)"]
        Coord --> VCP["VCP-1 Canonical Decision Record\n& Merkle Audit Log Anchor"]
    end
```
