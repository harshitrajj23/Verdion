# VERIDION Phase 5K — Deliverable 10: Defect and Remediation Register

## Defect Register (Phase 5K)

| ID | Component | Defect Description | Severity | Remediation | Verification Status |
| :---: | :--- | :--- | :---: | :--- | :---: |
| **DEF-5K-01** | `EvidenceGroundingService` | `has_failure` check omitted `UNVERIFIED` status, allowing unauthenticated sources to be treated as verified | **HIGH** | Added `GroundingStatus.UNVERIFIED.value` to fail-closed failure check | **RESOLVED & VERIFIED** |
| **DEF-5K-02** | Frontend Build | Next.js attempted online Google Font fetch in offline sandbox | **MEDIUM** | Configured offline font variables in `next.config.mjs` and `layout.tsx` | **RESOLVED & VERIFIED** |
| **DEF-5K-03** | Sandbox AsyncIO | Windows `ProactorEventLoop` socketpair creation hung in restricted sandbox | **MEDIUM** | Provided synchronous execution pathways (`execute_inference_sync`) | **RESOLVED & VERIFIED** |
| **DEF-5K-04** | Crypto Nonce Validation | Non-hex characters in digest raised ValueError instead of structured error | **LOW** | Enforced strict hex validation with explicit ValueError rejection | **RESOLVED & VERIFIED** |
