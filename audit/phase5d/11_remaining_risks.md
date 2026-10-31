# Phase 5D — Remaining Risks, Protocol Assumptions, and Honest Limitations

## Executive Summary

Auditability requires intellectual honesty. Claiming absolute guarantees where mathematical or operational boundaries exist destroys regulatory credibility.

This document records the remaining architectural risks, trust assumptions, and operational boundaries of VERIDION Option C following the Phase 5D adversarial audit.

---

## 1. Concrete Remaining Risks Matrix

| Risk Dimension | Threat Scenario | Mitigation Status | Remaining Limitation |
| :--- | :--- | :--- | :--- |
| **Privileged DBA Rewriting** | A rogue systems administrator with root SQLite access modifies an event at sequence $i$ and recalculates all subsequent hash pointers. | **Mitigated:** Exported decision records contain Merkle roots; verifier flags unanchored records. | Without an external on-chain or third-party attested checkpoint, a completely re-computed local database cannot be differentiated from authentic history. |
| **External Legal Portal Uptime** | Official EUR-Lex SPARQL or Curia endpoints experience outages, rate limiting, or HTML layout revisions. | **Mitigated:** Ingestion uses HTTPS caching and bundled fixtures as fallback; provenance flags `FALLBACK_FIXTURE`. | In live mode during external outages, real-time fetching of new amendments is blocked until upstream availability is restored. |
| **LLM Inference Stochasticity** | Re-executing an agent prompt with temperature $> 0.0$ generates divergent wording. | **Mitigated:** Decision records store exact model outputs, prompt versions, and completion digests. | Replaying a recorded decision record is 100% deterministic; rerunning a live LLM is nondeterministic and cannot guarantee identical phrasing. |
| **Smart Contract Cross-Contract Replay** | Identical `marketId` initialized in a different contract deployment on the same chain. | **Mitigated:** Fixed-width parameters prevent packing collisions; `chainId` prevents cross-chain replay. | Historical V1 contract does not include `contractAddress` in the packing tuple; V2 deployment should bind `address(this)`. |
| **Predictive Calibration Sample Size** | Projecting broad calibration accuracy from small sample sizes ($N < 50$). | **Mitigated:** ForecastEvaluator reports sample size and baseline comparisons explicitly. | ECE metrics on small datasets are statistically noisy; empirical calibration claims require continuous resolution over large cohorts. |
| **Blockchain Receipt Semantic Conflation** | Equating a confirmed Ethereum transaction receipt with legal compliance. | **Mitigated:** Clear UI and audit disclosures separating cryptographic inclusion from statutory truth. | A smart contract transaction proves only EVM block inclusion; it does not constitute formal legal counsel or judicial immunity. |

---

## 2. Operational Recommendations for Production Readiness

1. **Periodic L1/L2 Merkle Root Anchoring:**
   - Implement an automated scheduled daemon that aggregates the day's sealed decision records into a single daily Merkle root and submits a single `anchorDailyState(bytes32 dailyRoot)` transaction to Ethereum Sepolia or Arbitrum One.
2. **Contract V2 Migration for Full Domain Separation:**
   - In the next contract upgrade cycle, update `PredictionMarket.sol` to evaluate:
     `keccak256(abi.encodePacked(block.chainid, address(this), marketId, msg.sender, probabilityBps, evidenceDigest, nonce))`
   - Binding `address(this)` provides full domain separation against cross-contract replay.
3. **Multi-Region Evidence Mirroring:**
   - Maintain cold-storage IPFS or Arweave mirrors of official EUR-Lex CELEX regulations to eliminate single-point-of-failure reliance on European Commission web portals.
