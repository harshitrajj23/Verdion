# VERIDION PHASE 4 — INDEPENDENT BLOCKCHAIN VERIFICATION REPORT

**Document ID:** `audit/phase4/02_blockchain_external_verification.md`  
**Execution Timestamp:** 2026-10-27T07:05:00+05:30  
**Target EVM Network:** Ethereum Sepolia Testnet  
**Configured Chain ID:** `11155111`  
**Public RPC Endpoint Used for Verification:** `https://ethereum-sepolia-rpc.publicnode.com`  
**Etherscan Explorer URL:** `https://sepolia.etherscan.io`  

---

## 1. Executive Summary

In accordance with Phase 4 directives, an independent read-only blockchain verification was executed against the live Ethereum Sepolia network. Every contract address and transaction hash cited across repository configurations, deployment manifests, backend services, and previous audit reports was queried using standardized `eth_getCode` and `eth_getTransactionReceipt` RPC calls.

### Critical Verdict:
1. **The Purported Vanity Addresses (`0x1111...`, `0x2222...`, `0x3333...`, `0x4444...`, `0x5555...`):**
   - **Bytecode Length:** Exactly `0 bytes`.
   - **Status:** **UNVERIFIED / EMPTY ACCOUNT / INVALID FOR LIVE EXECUTION**.
   - **Root Cause Analysis:** These addresses were placeholder defaults hardcoded in `backend/app/core/config.py`. They have no contract code on Ethereum Sepolia and cannot process transactions.
2. **The Actual Deployed Manifest Contracts (`deployments.json`):**
   - **Status:** **CONFIRMED ON-CHAIN**.
   - All 5 smart contracts (`CaseRegistry`, `AgentRegistry`, `PredictionMarket`, `EvidenceBounty`, `ReputationSettlement`) exist on Sepolia with substantial verified runtime bytecode (3.9 KB to 19.5 KB) deployed in blocks `11997251` through `11997273`.
3. **The 9 Full-Lifecycle Transactions (`lifecycle_sepolia.json`):**
   - **Status:** **CONFIRMED ON-CHAIN**.
   - Every single transaction hash from the Sepolia lifecycle demo (from `registerAgent` through `settleMarket`) was independently verified. All 9 returned status `0x1` (success), valid block confirmations between `11997418` and `11997718`, and gas consumption matching verified EVM execution.

---

## 2. Network Identity & RPC Verification

- **Configured Chain ID:** `11155111` (matches Sepolia specification).
- **RPC Health Check:**
  - Endpoint: `https://ethereum-sepolia-rpc.publicnode.com`
  - Method: `eth_chainId` -> Returned `0xaa36a7` (Decimal `11155111`).
  - Method: `eth_blockNumber` -> Returned block `12001843` (active, advancing block production).

---

## 3. Comprehensive Contract Address Audit

| Contract Name | Address Queried | Bytecode Length | Target Chain | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **CaseRegistry (Config Placeholder)** | `0x1111111111111111111111111111111111111111` | `0 bytes` | Sepolia | **FAIL — Empty Account (Unverified)** |
| **AgentRegistry (Config Placeholder)** | `0x2222222222222222222222222222222222222222` | `0 bytes` | Sepolia | **FAIL — Empty Account (Unverified)** |
| **PredictionMarket (Config Placeholder)** | `0x3333333333333333333333333333333333333333` | `0 bytes` | Sepolia | **FAIL — Empty Account (Unverified)** |
| **EvidenceBounty (Config Placeholder)** | `0x4444444444444444444444444444444444444444` | `0 bytes` | Sepolia | **FAIL — Empty Account (Unverified)** |
| **ReputationSettlement (Config Placeholder)** | `0x5555555555555555555555555555555555555555` | `0 bytes` | Sepolia | **FAIL — Empty Account (Unverified)** |
| **CaseRegistry (Actual Deployment)** | `0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E` | `5,596 bytes` | Sepolia | **PASS — Confirmed Deployed Bytecode** |
| **AgentRegistry (Actual Deployment)** | `0x32d5D291e287fF173F803f5ee53Aef75BADb2006` | `3,912 bytes` | Sepolia | **PASS — Confirmed Deployed Bytecode** |
| **PredictionMarket (Actual Deployment)** | `0xFF5e85547E443e3d50b393E09885c6Eb9671EE27` | `19,508 bytes` | Sepolia | **PASS — Confirmed Deployed Bytecode** |
| **EvidenceBounty (Actual Deployment)** | `0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46` | `10,620 bytes` | Sepolia | **PASS — Confirmed Deployed Bytecode** |
| **ReputationSettlement (Actual Deployment)** | `0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c` | `6,466 bytes` | Sepolia | **PASS — Confirmed Deployed Bytecode** |

---

## 4. Sepolia On-Chain Transaction Receipt Verification

Each transaction from the Sepolia lifecycle artifact (`frontend/src/lib/lifecycle_sepolia.json`) was checked against the Sepolia public RPC node.

```
Step 'registerAgent':
  Tx Hash: 0x1f94f5085df2191495baf81a448bdc4d7965649e98e5177f11c494d7c0525d11
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997418 | Gas Used: 684,473
  To: 0x32d5D291e287fF173F803f5ee53Aef75BADb2006 (AgentRegistry)

Step 'createMarket':
  Tx Hash: 0xf5588b6c9bb37e63df3937cf9f4bb3e3e99140442596aa76b562d4578ad0c1c7
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997461 | Gas Used: 819,991
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'fundMarket':
  Tx Hash: 0x2a993f2f2668116ff7ab0e6c4bb70a233aefd325aaa71db90fafa12f524e86e5
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997462 | Gas Used: 379,985
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'publishMarket':
  Tx Hash: 0x104054e7082b47a7b262c9b552d0efd294e3521a3bea7e3ce8aa9a6627b1a6ae
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997463 | Gas Used: 133,793
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'commitForecast':
  Tx Hash: 0xb6adb372a41a4b5e2a8d9f0c432ad27df62175f0dc7d67dc0bc0b850ace4908e
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997464 | Gas Used: 588,702
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'closeMarket':
  Tx Hash: 0xaadb64b6f1ecbb49c58487838c62d55bbbc2c1b168b869678e7f07f310b055b1
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997471 | Gas Used: 33,524
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'revealForecast':
  Tx Hash: 0xc6365643831ced46cc294393283e1f06f7128f30b564c42edbe8ca8126764815
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997472 | Gas Used: 701,995
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'proposeResolution':
  Tx Hash: 0x540fa04a63548c7d86e8dfbef3342e7dfd2daab82e77bbd9efcd5a0a0c8c9f52
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997482 | Gas Used: 259,949
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)

Step 'settleMarket':
  Tx Hash: 0x220d460591302025e7f12d621399e2ab15724979678b4aed92ec2d2970e989e4
  Receipt Status: 0x1 (CONFIRMED) | Block: 11997718 | Gas Used: 975,238
  To: 0xFF5e85547E443e3d50b393E09885c6Eb9671EE27 (PredictionMarket)
```

---

## 5. Architectural Remediation & Code Changes

To align the codebase with reality and eliminate deception:

1. **Update `backend/app/core/config.py`:**
   - Automatically call `load_deployments()` upon initialization.
   - Replace the fallback placeholders `0x1111...` with the actual confirmed deployment addresses from `deployments.json`.
2. **Refactor `BlockchainService.record_simulated_transaction`:**
   - Explicitly tag simulated transactions with `execution_mode: "LOCAL_SIMULATION"`.
   - Never generate phantom Etherscan links (`https://sepolia.etherscan.io/tx/{simulated_hash}`). Set `explorer_url = None` for simulated transactions.
   - Display status as `"SIMULATED_LOCAL"` or `"PERSISTED_OFFCHAIN"`, reserving `"CONFIRMED_ONCHAIN"` strictly for receipts verified against a live RPC node.
3. **Add Live RPC Verification Method:**
   - Implemented `BlockchainService.verify_onchain_receipt(tx_hash: str)` which performs real read-only verification over Web3 / RPC to confirm block status, gas used, and event logs.
