# VERIDION Phase 2 Audit — 10: Honest Disclosure of Remaining Risks & Limitations

**Audit Date**: 2026-10-27T06:10:00+05:30  
**Audit Purpose**: Complete Intellectual Honesty Regarding Technical Boundaries, Assumptions, and Future Roadmap  
**Deliverable**: `audit/phase2/10_remaining_risks_and_limitations.md`  

---

## 1. Remaining Technical Risks & Architectural Limitations

### 1. Small In-Sample Sample Size ($N = 14$ Train / $N = 6$ Held-Out)
- **Limitation**: While the point estimate indicates a 34.2% error reduction over the base rate (Brier 0.1611 vs 0.2449) and a $+0.3042$ separation, the 95% bootstrap confidence interval ($[-0.1824, +0.0309]$) spans zero.
- **Risk**: A technical judge could note that in-sample superiority is not statistically distinguishable from zero at the 95% confidence level.
- **Mitigation & Path**: Transparently acknowledge the sample constraint in presentations. Do not claim statistical superiority; highlight that the protocol provides an open-source evaluation framework ready for community scaling ($N \ge 100$).

### 2. Local Model Inference Latency (~2.5 Minutes per Swarm Run)
- **Limitation**: Executing 4 sequential 7B parameter LLM calls on local CPU/GPU hardware requires 2 to 3 minutes per case.
- **Risk**: Waiting 3 minutes during a 3-minute hackathon pitch will cause the demo to stall.
- **Mitigation**: Use the pre-seeded demo endpoint (`POST /api/v1/demo/seed`) during live judging, which loads pre-computed agent outputs and Sepolia transaction receipts in $< 200 \text{ ms}$. Reserve live model generation for technical breakout sessions.

### 3. Evaluator Oracle Centralization
- **Limitation**: Prediction markets and bounties are resolved by the authorized `evaluator_address` in the current MVP.
- **Risk**: A compromised evaluator key could propose incorrect market resolutions.
- **Mitigation**: The protocol enforces a **24-hour challenge window** where network participants can counter-stake. In production, this will transition to a multi-agent Schelling-point consensus protocol (UMA / Kleros dispute pattern).

### 4. Jurisdiction Corpus Coverage
- **Limitation**: The curated regulatory corpus currently covers EU GDPR, EU AI Act, and US FTC Act.
- **Mitigation**: The retrieval architecture is modular; new statutes can be ingested simply by adding canonical JSON digests to `curated_corpus.json`.

---

## 2. Risk Mitigation Matrix

| Identified Risk | Severity | Implemented Mitigation | Remaining Work for Mainnet |
|---|:---:|---|---|
| **Small Sample Size** | Medium | Rigorous 14 train / 6 frozen held-out split (`FREEZE.md`) | Expand benchmark to $N \ge 100$ legal cases |
| **Demo Pitch Latency** | High | Instant vertical slice demo seed endpoint (`/demo/seed`) | Parallelize model prompt dispatch |
| **Oracle Compromise** | Medium | 24-hour community challenge window before settlement | Multi-signature decentralized dispute DAO |
| **Statutory Coverage** | Low | Modular SHA-256 corpus indexing architecture | Ingest UK GDPR, CCPA, and NIST AI RMF |
| **Formal Verification** | Low | Comprehensive 627-line Foundry invariant test suite | Certora / Halmos formal verification proofs |
