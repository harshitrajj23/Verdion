# Phase 5C — Option C Architecture: Auditable Regulatory Decision Infrastructure

## Executive Summary

Phase 5C definitively realigns **VERIDION** to **Option C: Auditable Regulatory Decision Infrastructure**. VERIDION is not a legal research chatbot, a toy multi-agent demo, a speculative prediction market, or a blockchain showcase. Its primary product property is **auditability** — enabling an independent reviewer or regulator to establish cryptographically and reproducibly:

1. What evidence was available at the exact moment of decision.
2. Where that evidence originated (EUR-Lex, CJEU/CURIA, EDPB official repositories).
3. Which specific version and content digest of each document was utilized.
4. Which analysis configuration, prompt versions, and agent software versions produced a conclusion.
5. What exact claims, passage citations, and counterarguments were registered.
6. Which regulatory forecasts were committed to *before* real-world outcomes were known.
7. Whether commitments and reveals conformed to strict cryptographic integrity.
8. How and by whom results were resolved under pre-declared criteria.
9. Which state elements were anchored on-chain and which remained off-chain.
10. Whether the entire decision chain can be independently verified without trusting the frontend, agents, or backend database.

---

## The Five Integrated Subsystems

```
                                  +------------------------------------------------+
                                  | 1. EVIDENCE PROVENANCE & VERSIONING            |
                                  | - Stable IDs (CELEX, ECLI, EDPB Guidelines)    |
                                  | - Immutable Content Digests (SHA-256)          |
                                  | - Exact Passage Extractor & Normalization      |
                                  +-----------------------+------------------------+
                                                          |
                                                          v
                                  +------------------------------------------------+
                                  | 2. REPRODUCIBLE ANALYSIS & DECISION ENGINE     |
                                  | - Versioned Scope (dec_<case_id>_v<version>)   |
                                  | - Canonical JSON RFC 8785 + NFC Hashing        |
                                  | - Grounded Claims & Adversarial Objections     |
                                  +-----------------------+------------------------+
                                                          |
                                                          v
                                  +------------------------------------------------+
                                  | 3. FORECASTING & COMMIT-REVEAL SUBSYSTEM       |
                                  | - Pre-Outcome Binding: keccak256(m||o||nonce)  |
                                  | - Strict Timing Windows & Nonce Secrecy        |
                                  | - Proper Scoring Rules (Brier & Binary LogLoss)|
                                  +-----------------------+------------------------+
                                                          |
                       +----------------------------------+----------------------------------+
                       |                                                                     |
                       v                                                                     v
+------------------------------------------------+                  +------------------------------------------------+
| 4. ON-CHAIN EVIDENCE & ANCHORING BOUNDARY      |                  | 5. INDEPENDENT AUDIT VERIFIER & EXPORT         |
| - Compact Hashes & Merkle Root Checkpoints     |                  | - Standalone Zero-Trust Verification Engine    |
| - Authorized Settlement & State Transitions    |                  | - Tamper Detection (Modify, Delete, Reorder)   |
| - Off-Chain Privacy for Prompts & Documents    |                  | - Exportable JSON Zip Packages with Manifest   |
+------------------------------------------------+                  +------------------------------------------------+
```

### Subsystem 1: Evidence Provenance and Versioning
- **Canonical Model:** `EvidenceSourceRecord` and `EvidencePassageRecord` (`backend/app/schemas/decision_record.py`).
- **Data Capture:** Originating publisher, official document identifiers (e.g., `32016R0679` for GDPR, `62018CJ0311` for Schrems II), canonical URLs, retrieval timestamps, normalization procedure version (`v1.0-clean_whitespace`), SHA-256 document content digest, and character-level passage selectors (`char_start`, `char_end`, `passage_digest`).
- **Disclaimers:** A cryptographic hash strictly proves data integrity and exact text immutability; it does **not** assert legal truth or statutory correctness.

### Subsystem 2: Reproducible Analysis
- **Canonical Model:** `CanonicalDecisionRecord` (`backend/app/schemas/decision_record.py`).
- **Scope & Configuration:** Bound to deterministic factual scope version, engine version (`veridion-engine-5c-v1.0.0`), dependency versions, model configuration, deterministic rule evaluation results, and timestamp.
- **Claims & Counterarguments:** Every claim references exact passage IDs with support confidence assessments. The synthesis agent captures minority objections and unresolved statutory ambiguities.
- **Replay vs. Rerun:** The decision engine records exact model completions for determinism. Rerunning stochastic LLM endpoints is distinguished from verifiable replay of the recorded decision record.

### Subsystem 3: Forecasting and Commit-Reveal
- **Canonical Model:** `ForecastMarketRecord`, `ForecastCommitmentRecord`, and `SettlementRecord`.
- **Pre-Outcome Commitments:** Forecasters submit `keccak256(abi.encodePacked(market_id, outcome, nonce))` prior to the trading deadline.
- **Reveal Protocol:** After trading closes and before the reveal deadline, the outcome and 256-bit secret nonce are revealed and verified against the pre-image hash.
- **Resolution & Settlement:** Authorized evaluators resolve outcomes based on pre-declared criteria. Brier scores and log loss are deterministically scored, preventing duplicate or premature settlement.

### Subsystem 4: On-Chain Evidence and Anchoring Boundary
- **On-Chain Elements:** Keccak256 commitment digests, reveal state transitions, Merkle root checkpoints, and authorized settlement payouts.
- **Off-Chain Elements:** Full legal source texts, raw prompts containing proprietary reasoning, forecaster nonces prior to reveal, and internal claim drafts.
- **Asset Separation:** Explicit separation between `LOCAL_SIMULATION` credits and `ON_CHAIN_SEPOLIA` transactions.

### Subsystem 5: Independent Audit and Verification
- **Verification Engine:** `AuditVerifier` (`backend/app/services/audit_verifier.py`).
- **Offline Capabilities:** Independent reviewers can execute the verifier via Python script or CLI without network access, verifying:
  1. Canonical decision record digest.
  2. Document and passage provenance.
  3. Claim citation grounding.
  4. Cryptographic commit-reveal hash matching.
  5. Brier score recalculation.
  6. Audit trail hash chain continuity and Merkle root checkpoints.

---

## What Option C Guarantees vs. What It Does Not Guarantee

| Dimension | Option C Guarantee | Explicit Non-Guarantee |
| :--- | :--- | :--- |
| **Document Integrity** | Document text has not changed by a single bit since retrieval (SHA-256 verified). | Does NOT guarantee the statute is currently in force or legally sound. |
| **Claim Grounding** | Claims cite exact byte/character offsets in verified documents. | Does NOT guarantee the judicial conclusion is legally infallible. |
| **Audit Log Integrity** | Application-level hash chaining detects deletion, reordering, or payload alteration. | Does NOT prevent a privileged DB root user from recalculating the whole chain without external Merkle checkpoints. |
| **Forecaster Integrity** | Predictions were irrevocably chosen *before* market closure without forecaster insight into opponent predictions. | Does NOT guarantee forecasters possess superior domain competence. |
| **Scoring Determinism** | Brier scores and reputation adjustments are calculated strictly by mathematical formula. | Does NOT guarantee economic incentives are sufficient in all low-volume regimes. |
| **Blockchain Finality** | Transaction inclusion and smart contract state enforcement on EVM. | A successful transaction receipt does NOT equate to statutory compliance. |

---

## Architectural Compatibility & Preservation

All existing Phase 1 through 5B infrastructure is preserved without regression:
1. **Live Legal Sources:** EUR-Lex SPARQL/REST, CJEU/CURIA scraping, and EDPB guideline adapters remain active.
2. **700 Historical Audit Records:** Preserved in SQLite `veridion.db` and backfilled with continuous hash links (`sequence_number`, `previous_event_digest`, `event_digest`).
3. **Smart Contracts:** Existing `CaseRegistry`, `AgentRegistry`, `PredictionMarket`, `EvidenceBounty`, and `ReputationSettlement` contracts remain valid.
4. **Test Suite:** All 123 backend regression tests and Next.js frontend builds compile cleanly.
