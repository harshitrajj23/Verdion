# Phase 5D — On-Chain Anchor Verification & Deployment Boundary

## Executive Summary

A core directive of Phase 5D is that an audit system must never deceive reviewers by presenting simulated local state, database rows, or phantom transaction hashes as genuine on-chain anchors.

This assessment inspects the deployed contract identities in [`backend/contracts/deployments.json`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/contracts/deployments.json), verifies the actual runtime execution modes, and defines the explicit trust classifications between local simulations and confirmed external anchors.

---

## 1. Verified Contract Deployments on Ethereum Sepolia

The repository contains verified contract deployment records targeting Ethereum Sepolia (Chain ID `11155111`):

| Contract Name | Deployed Address on Sepolia | Core Protocol Responsibility | Source Code Reference |
| :--- | :--- | :--- | :--- |
| **CaseRegistry** | `0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E` | Case scope registration, scope versioning, and Merkle root anchoring. | [`CaseRegistry.sol`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/contracts/src/CaseRegistry.sol) |
| **AgentRegistry** | `0x32d5D291e287fF173F803f5ee53Aef75BADb2006` | Agent identity registration, role validation, and authorization flags. | [`AgentRegistry.sol`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/contracts/src/AgentRegistry.sol) |
| **PredictionMarket** | `0xFF5e85547E443e3d50b393E09885c6Eb9671EE27` | Commit-reveal forecast markets, challenge windows, and proper scoring. | [`PredictionMarket.sol`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/contracts/src/PredictionMarket.sol) |
| **EvidenceBounty** | `0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46` | Evidence bounties, submission deduplication, and challenge periods. | [`EvidenceBounty.sol`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/contracts/src/EvidenceBounty.sol) |
| **ReputationSettlement** | `0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c` | Credit balance ledger, payout distribution, and reputation scoring. | [`ReputationSettlement.sol`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/contracts/src/ReputationSettlement.sol) |

---

## 2. Actual Runtime Execution State: Local Simulation vs. On-Chain

Inspection of runtime database records in SQLite `veridion.db` and [`BlockchainService.record_simulated_transaction`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/services/blockchain_service.py#L67-L107) establishes the following truth:

1. **Default Mode is `LOCAL_SIMULATION`:**
   - Every transaction generated during normal web app interaction and multi-agent workflow is explicitly tagged with `execution_mode: "LOCAL_SIMULATION"` and `is_simulated: True`.
   - The system strictly sets `explorer_url = None` for simulated transactions. It does **not** fabricate phantom Etherscan links.
2. **On-Chain Verification via RPC:**
   - [`BlockchainService.verify_onchain_receipt(tx_hash)`](file:///c:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/services/blockchain_service.py#L109-L140) queries live Sepolia nodes via `eth_getTransactionReceipt`.
   - When public RPC nodes time out or return rate limits (as demonstrated during Phase 5D RPC testing), the system gracefully reports unverified status rather than inventing confirmed receipts.
3. **No Unauthorized Funds Spent:**
   - In accordance with the Phase 5D primary directive, no live funds were spent, no new contracts were deployed, and no write transactions were submitted to Sepolia without explicit authorization.

---

## 3. The Five Strict Trust Classifications

To prevent semantic conflation, VERIDION classifies every decision record and transaction into one of five unambiguous states:

| Classification | Technical Meaning | Verification Authority |
| :--- | :--- | :--- |
| **`LOCAL_SIMULATION`** | Internal simulated ledger update within local SQLite database. Simulates contract behavior without broadcasting to Ethereum. | Internal database hash-chain only. |
| **`LOCAL_EVM`** | Deterministic EVM test execution within an isolated Foundry or Hardhat local node. | Local EVM test runner. |
| **`UNANCHORED_LOCAL_RECORD`** | The decision record and audit log are internally valid, but the Merkle root has **not** been anchored to an external blockchain block. | Internal verifier (marked `UNVERIFIED` anchor). |
| **`EXTERNALLY_ANCHORED`** | The Merkle root has been published to a confirmed on-chain transaction or independently attested checkpoint. | External consensus (Ethereum Sepolia / Mainnet). |
| **`ON_CHAIN_CONFIRMED`** | A transaction receipt with `status = 0x1` verified by querying an Ethereum RPC node. | EVM block inclusion proof. |

> **Audit Guarantee:** The offline verifier marks packages lacking external checkpoints as `UNANCHORED`, warning reviewers that a privileged database administrator could theoretically rewrite historical records.
