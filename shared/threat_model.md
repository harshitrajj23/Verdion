# Verdion Threat Model & Security Specification (§17.1, §17.2)

## 1. Threat Matrix & Mitigations

| Threat ID | Threat Description | Attack Vector | Protocol Mitigation | Verification Mechanism |
|-----------|--------------------|---------------|---------------------|------------------------|
| **TH-01** | Prompt Injection in Retrieved Source | Malicious or adversary-controlled text injected into statutory passage instructing agent to ignore rules. | Strict data isolation fences; retrieved content treated as passive text; restricted tool execution; schema output enforcement. | Unit tests verifying embedded injection strings fail to alter agent policy (FR-012). |
| **TH-02** | Fabricated Citations ("Hallucinations") | LLM generates convincing but fictitious court citations or statute numbers. | Deterministic passage verification against source digest; evidence linking required for material claims. | EvidenceVerifier agent checks document_id against corpus hash (FR-008, FR-026). |
| **TH-03** | Outdated or Superseded Authority | Applying repealed laws or old regulatory guidance. | Mandatory effective-date metadata and jurisdiction tagging. | Rule engine checks effective dates against case assessment date (FR-010). |
| **TH-04** | Agent Collusion & Manufactured Consensus | Sybil agents copying another agent's forecast or submitting identical correlated claims. | Commit-reveal protocol prevents forecast frontrunning; correlation tracking across agents; model diversity checks. | Commitments require salt nonces; off-chain variance and disagreement metrics (FR-033, FR-034). |
| **TH-05** | Replay & Front-running Attacks | Submitting a previously used commitment hash or front-running a revealed forecast. | Canonical encoding includes `chainId`, `marketId`, `agentAddress`, and `nonce`. Replay reverts on-chain. | Foundry unit test `testReplayAttackFails` (§18.5). |
| **TH-06** | Malicious / Spam Evidence Submissions | Flooding bounty with low-quality, duplicate, or irrelevant text. | Canonical digest duplicate checks, reviewer acceptance rubric, challenge window, credit bonding. | Duplicate digest reverts; reviewer must score against 6 rubric criteria (FR-045, FR-046). |
| **TH-07** | Duplicate / Reentrant Settlement | Calling settlement multiple times to drain simulated credits or inflate reputation. | ReentrancyGuard, state machine check `require(status != SETTLED)`, idempotent accounting. | Foundry test `testDuplicateSettlementReverts` (FR-052). |
| **TH-08** | Unauthorized Resolution | Attacker impersonating evaluator or calling resolution functions. | Role-based access control (`onlyEvaluator`, `onlyAdmin`), timelocked challenge periods. | Foundry test `testUnauthorizedResolutionFails` (FR-044). |
| **TH-09** | Private / Sensitive Data Exposure | Leaking confidential corporate case facts on public blockchain. | Strict on-chain / off-chain separation: only hashes, IDs, and numeric bounds stored on-chain. | Zero plaintext case facts in contract storage or events (FR-054..058). |

---

## 2. Smart Contract Guardrails (§17.2)
1. **Explicit State Transitions**: Enforce `DRAFT -> PUBLISHED -> REVEAL -> CLOSED -> RESOLUTION_PROPOSED -> CHALLENGE -> SETTLED / VOID`.
2. **Commit-Reveal Invariants**:
   - $\text{commitment} = \text{keccak256}(\text{abi.encodePacked}(\text{chainId}, \text{marketId}, \text{agentAddress}, \text{probabilityBps}, \text{evidenceDigest}, \text{nonce}))$
   - Reveal window only unlocks after commitment deadline passes.
   - Non-matching reveals emit `CommitmentMismatch` and forfeit deposits.
3. **Emergency Pause**: Pausable by administrative role to halt markets/bounties during unexpected RPC forks or critical incidents.
4. **Trust Model Note**: In this MVP, challenges are resolved by the protocol admin, who is also the evaluator.

