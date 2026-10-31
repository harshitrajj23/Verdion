# Phase 5C — On-Chain vs. Off-Chain Architectural Boundary

## Overview

A common antipattern in decentralized systems is attempting to store large legal texts, AI model prompts, or sensitive company data directly on public blockchains, or conversely, using a centralized database while branding the project as "on-chain."

Option C establishes a **strict, auditable boundary** governing exactly what state transitions are executed on-chain versus preserved off-chain.

---

## 1. Boundary Matrix

| System Component | Execution Location | Storage Mechanism | Cryptographic Anchor | Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Legal Corpus Texts** | Off-chain | Document Store / Cache | SHA-256 Content Digest | Multi-megabyte regulations (GDPR, AI Act) are economically prohibitive and unnecessary to store on EVM. |
| **Passage Excerpts** | Off-chain | SQLite / JSON Store | SHA-256 Passage Digest | Offsets and excerpt hashes allow complete verification without EVM bloat. |
| **Agent Reasoning & Prompts** | Off-chain | Backend Execution Engine | SHA-256 Output Digest | Prompts contain trade secrets, intermediate agent interactions, and potential sensitive identifiers. |
| **Forecaster Commitments** | On-chain & Off-chain | Smart Contract / DB | Keccak-256 Hash | Irrevocably timestamps forecaster predictions before the market trading deadline. |
| **Reveals (Outcome + Nonce)** | On-chain & Off-chain | Smart Contract / DB | Pre-image Match | State transition enforces verifiable reveal within the allocated time window. |
| **Audit Event Stream** | Off-chain | Database Hash-Chain | Sequential SHA-256 Chain | High-frequency logging (hundreds of events) would saturate block space. |
| **Audit Checkpoints** | On-chain | Smart Contract State | Merkle Root (Bytes32) | Compact 32-byte Merkle root anchors the entire history of hundreds of off-chain audit events. |
| **Settlement Payouts** | Optional On-chain / Off-chain | Smart Contract / Local Ledger | Transaction Receipt | Real fund transfers require EVM execution; simulated paper trading remains in local credits. |

---

## 2. On-Chain Anchoring Architecture

```
+----------------------------------------------------------------------------------+
| OFF-CHAIN DECISION RECORD                                                        |
| - Case question, factual scope, agent prompts                                    |
| - Evidence documents (SHA-256: 4a5e3...)                                         |
| - Grounded claims, counterarguments, synthesis                                   |
| - Audit Event Stream (Events #1 to #700, hash-chained)                           |
+----------------------------------------+-----------------------------------------+
                                         |
                                         | Binary Merkle Tree
                                         v
+----------------------------------------------------------------------------------+
| CANONICAL MERKLE ROOT: 0x9f83e20...7a12b                                         |
+----------------------------------------+-----------------------------------------+
                                         |
                                         | Anchor Transaction (bytes32 root)
                                         v
+----------------------------------------------------------------------------------+
| ON-CHAIN SMART CONTRACT (CaseRegistry / PredictionMarket)                        |
| - Publicly verifiable block timestamp and block number                           |
| - Immutable event emission (DecisionAnchored(caseId, merkleRoot, timestamp))     |
| - Unforgeable history protected by Ethereum network consensus                    |
+----------------------------------------------------------------------------------+
```

---

## 3. Privacy, Secret Leakage, and GDPR Compliance

1. **No Sensitive PII On-Chain:** Public blockchains are permanent and immutable. Under GDPR Article 17 ("Right to Erasure"), personal data stored on-chain violates European privacy regulations. Option C ensures no customer names, proprietary case scenarios, or un-anonymized party identifiers are ever written to the blockchain.
2. **Pre-Reveal Nonce Secrecy:** Nonces are retained in secure forecaster storage or client sessions and never transmitted to public or audit endpoints until the reveal phase begins.
3. **Transaction Receipt Semantic Disclaimer:**
   > A successful Ethereum transaction receipt proves only that an EVM state transition was accepted into a mined block. It does **NOT** prove that the underlying legal reasoning is correct, that the evidence was uncorrupted at origin, or that a regulatory authority will agree with the decision.
