# VERIDION PHASE 3 — REMAINING BLOCKERS & SYSTEM LIMITATIONS
**Document Reference:** `audit/phase3/11_remaining_blockers.md`  
**Evaluation Standard:** PRD Section 17 & Section 15  
**Timestamp:** 2026-10-27T06:44:40Z  
**Branch:** `Divyank`

---

## 1. External Credentials & Environmental Prerequisites

While VERIDION is 100% operational locally with SQLite persistence, deterministic hybrid verification, and Sepolia simulator contracts, the following optional external integrations require user-provided credentials for public network deployment:

| Integration | Required Credential / Variable | Current Behavior Without Credential | Production Impact |
| :--- | :--- | :--- | :--- |
| **Fine-Tuned Legal LLM** | `HF_API_TOKEN` / `HF_ENDPOINT_URL` | Transparently falls back to deterministic statutory rule engine (`GDPR Art 6(1)(f) & Art 89(1)`), clearly flagged in claim metadata. | High-quality deterministic rules execute; generative nuances require dedicated endpoint. |
| **Sepolia Testnet RPC** | `SEPOLIA_RPC_URL` & `PRIVATE_KEY` | Off-chain SQLite transaction receipts and local protocol simulator are used; recorded Sepolia lifecycle is displayed for verification. | Real-time wallet broadcasting requires funded Sepolia testnet wallet. |
| **Production Blockchain** | Mainnet Deployment Approval | Strictly uninitialized and disabled per instructions. | Real financial assets are never risked. |

---

## 2. Known Legal Intelligence & Technical Limitations

1. **Statutory Scope:** The current deterministic legal rule engine prioritizes European Union (GDPR, EU AI Act), California (CPRA/CCPA), and general privacy frameworks. Expanding to specialized tax, patent, or maritime jurisdictions requires encoding additional statutory rule trees.
2. **Deterministic Fallback vs. Open-Domain Dialogue:** When offline, adversarial arguments follow deterministic statutory exception templates rather than dynamic generative synthesis.
3. **Synthetic Simulated Credits:** In local mode, credits are protocol simulation units rather than ERC-20 tokens with secondary market liquidity.
4. **Held-Out Benchmark Split Protection:** As documented in Phase 2, held-out benchmark scenarios (`scen_15` through `scen_20`) remain quarantined from live training pipelines to prevent benchmark contamination.

---

## 3. Next Highest-Impact Engineering Improvement

**Automated Court Docket Ingestion (PACER / CJEU InfoCuria Webhook Connector):**
Building a continuous ingestion crawler that automatically downloads newly published CJEU and Federal appellate court opinions, computes SHA-256 digests in real time, and triggers automated regression bounties on existing frozen argument graphs.
