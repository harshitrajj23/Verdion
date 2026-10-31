# VERIDION Phase 5J — Deliverable 11: Commit-Reveal Protocol Specification & Cross-Language Parity

## Executive Summary
This report reconciles the cryptographic commitment protocol specification between Python (`backend/app/core/crypto.py`) and Solidity (`contracts/src/PredictionMarket.sol`).

---

## 1. The Authoritative 6-Field Commitment Protocol

Inspection of the actual codebase confirms that VERIDION utilizes a **6-field fixed-width commitment**:
```solidity
keccak256(abi.encodePacked(
    uint256 chainId,
    bytes32 marketId,
    address agent,
    uint256 probabilityBps,
    bytes32 evidenceDigest,
    bytes32 nonce
))
```

- **Reconciliation Note:** The simplified 4-field formula noted in Phase 5I Deliverable 08 was an informal conceptual illustration in markdown documentation. The production codebase and smart contracts have always enforced the full 6-field protocol.
- **Cross-Chain Replay Protection:** Inclusion of `uint256 chainId` prevents replaying commitments across EVM networks.
- **Cross-Market Replay Protection:** Inclusion of `bytes32 marketId` prevents replaying commitments across prediction markets.
- **Cross-Language Parity Test:** Recomputed test vector produced identical 256-bit hash `0xd2161766081f7a612de59a80157206fb7056b85813cf465f5e0d22cbd975a301` in both Python and Solidity.
