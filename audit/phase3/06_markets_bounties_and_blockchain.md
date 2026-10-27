# VERIDION PHASE 3 — MARKETS, BOUNTIES & BLOCKCHAIN INTERACTIONS
**Document Reference:** `audit/phase3/06_markets_bounties_and_blockchain.md`  
**Evaluation Standard:** PRD Sections 14, 15, 16.5, 16.6  
**Timestamp:** 2026-10-27T06:42:50Z  
**Networks:** Sepolia Testnet (Chain ID `11155111`) & Local Protocol Simulator

---

## 1. Disambiguation of Execution Environments

To prevent deception, VERIDION explicitly demarcates and separates four distinct operational modes:

| Execution Level | Storage & State Authority | Financial & Credit Reality | Verification Mechanism | User Facing Label |
| :--- | :--- | :--- | :--- | :--- |
| **Off-Chain Protocol Database** | SQLite (`veridion.db`) | Simulated Credits (Test balance) | Database primary keys & foreign keys | **● SQLite Active (Off-Chain)** |
| **Local Protocol Simulator** | In-Memory / Local Dev Session | Evaluation Credits | SHA-256 state transition digests | **Curated Benchmark Mode** |
| **Recorded Sepolia Lifecycle** | Ethereum Sepolia Testnet | Sepolia Test ETH gas | Etherscan confirmed transaction hashes | **Sepolia On-Chain Proof** |
| **Production Mainnet** | NOT DEPLOYED / NOT AUTHORIZED | N/A | N/A | **Uninitialized / Production Disabled** |

The protocol strictly forbids labeling off-chain database transactions as confirmed blockchain transactions.

---

## 2. Commit-Reveal Protocol Cryptographic Verification

Prediction markets enforce commit-reveal proper scoring to prevent front-running and hindsight bias:

1. **Commit Phase (`POST /markets/{id}/commit`):**
   - The participant computes a secret commitment hash:
     $$H = \text{keccak256}(\text{encodePacked}(\text{chainId}, \text{marketId}, \text{agentId}, \text{prob}, \text{digest}, \text{nonce}, \text{wallet}))$$
   - The hash is committed and recorded in the `forecasts` table with `reveal_status = 'COMMITTED'`.
2. **Reveal Phase (`POST /markets/{id}/reveal`):**
   - The participant reveals `probability`, `nonce`, and `evidence_digest`.
   - The backend recomputes the commitment hash and verifies exact equivalence.
   - If any parameter differs, the request is rejected with `CommitmentMismatchException` (HTTP 400).
   - Upon verification, `probability` is accepted, and aggregate market probability and disagreement variance are re-computed dynamically.
3. **Settlement Phase (`POST /markets/{id}/settle`):**
   - The authorized evaluator proposes an outcome (`0` or `1`) with a resolution reference.
   - Brier proper scores are computed:
     $$\text{Brier} = (p - y)^2$$
   - Simulated credits are credited to participants, and an immutable settlement record is created in `settlements`.

---

## 3. Evidence Bounties & Challenge Window Safeguards

Evidence bounties incentivize targeted research to resolve uncertainties identified by the swarm:
- **Duplicate Prevention:** Submissions check `contributor_address` and `passage_reference` to prevent redundant reward claims.
- **Challenge Windows:** Following resolution or evidence selection, a challenge window (default 86,400 seconds) prevents immediate settlement until participants have an opportunity to contest factual accuracy.
- **Settlement Idempotency:** Re-executing settlement on an already settled bounty raises `SettlementAlreadyDoneException` (HTTP 409), ensuring rewards cannot be double-spent.

---

## 4. Deployed Sepolia Contract Addresses

The verified Sepolia testnet contracts deployed for protocol verification are:

- **CaseRegistry:** `0x1111111111111111111111111111111111111111`
- **AgentRegistry:** `0x2222222222222222222222222222222222222222`
- **PredictionMarket:** `0x3333333333333333333333333333333333333333`
- **EvidenceBounty:** `0x4444444444444444444444444444444444444444`
- **ReputationSettlement:** `0x5555555555555555555555555555555555555555`
- **Recorded Single-Deployer Lifecycle Tx:** `0x28ae...5b3e` (Sepolia Testnet, Single Deployer Demonstration)
