# Verdion End-to-End Demo Script (PRD Appendix A)

This script provides an exact step-by-step walkthrough of the VERIDION protocol for hackathon evaluation and demonstration.

---

## Scenario: AI-Powered Customer Analytics Compliance Case
- **Subject**: AI startup processing user customer-support conversations to train and refine a customer service LLM.
- **Jurisdiction**: European Union (GDPR & EU AI Act).
- **Assessment Date**: 2026-03-15.
- **Key Question**: Does secondary processing of customer transcripts for LLM pre-training constitute an incompatible purpose under GDPR Article 6(4) / Article 5(1)(b) absent explicit renewed consent?

---

## Step 1: Case Creation & Scope Validation (§6.1, FR-001)
1. **Action**: Navigate to `/cases` and initialize case `case_euaia_001`.
2. **Input Facts**:
   - `processing_purpose`: "customer service AI fine-tuning and sentiment analytics"
   - `data_categories`: ["unredacted customer support chats", "account identifiers"]
   - `user_consent_mechanism`: "initial terms of service acceptance"
3. **Outcome**:
   - Backend freezes scope version `1`.
   - Missing-fact detector flags: *Missing retention schedule for raw embeddings* and *No purpose specification for third-party foundation models*.

---

## Step 2: Multi-Agent Swarm Investigation (§6.2, FR-013..017)
1. **Researcher Agent**: Retrieves Article 5(1)(b) (Purpose Limitation), Article 6(4) (Compatibility Test), and EDPB Guidelines 4/2019. Records canonical source digests.
2. **Interpreter Agent**: Maps chat logs to "special category data risk" and identifies that generic terms-of-service consent does not satisfy specific purpose criteria.
3. **Adversarial Agent**: Challenges the hypothesis by asserting legitimate interest under Article 6(1)(f) and commercial product safety refinement exemptions.
4. **Verifier Agent**: Checks passage hashes against source corpus. Confirms 3 citations, flags 1 unsupported claim regarding statutory safe-harbor.
5. **Coordinator Agent**:
   - Synthesizes findings into the Argument Graph (`support`, `contradiction`, `qualify` edges).
   - Calculates uncertainty priority: $\text{Priority} = 0.85 \times 0.70 \times 0.90 = 0.535$.

---

## Step 3: Prediction Market Lifecycle (§6.3, §10, FR-031..039)
1. **Market Creation**: Market `mkt_gdpr_001` opened: *"Will an independent regulatory evaluator find the secondary training workflow non-compliant with GDPR Article 6(4)?"*
2. **Commit Phase**:
   - Agent 1 commits $H(\text{chainId}, \text{marketId}, \text{agent1}, 8000, \text{eviDigest}, \text{nonce1})$
   - Agent 2 commits $H(\text{chainId}, \text{marketId}, \text{agent2}, 6500, \text{eviDigest}, \text{nonce2})$
   - Agent 3 commits $H(\text{chainId}, \text{marketId}, \text{agent3}, 4500, \text{eviDigest}, \text{nonce3})$
3. **Reveal Phase**: Agents reveal nonces and probabilities on-chain.
4. **Aggregation**:
   - Unweighted mean: $p = (0.80 + 0.65 + 0.45) / 3 = 63.3\%$
   - Disagreement variance: $D = 0.0205$ (triggers targeted evidence bounty).

---

## Step 4: Evidence Bounty & Challenge (§6.4, §11, FR-040..046)
1. **Bounty Opened**: 100 simulated credits offered for authoritative EDPB or CJEU precedent on AI fine-tuning as an incompatible purpose.
2. **Evidence Submission**: Contributor submits EDPB Statement 01/2024 with passage reference and cryptographic digest.
3. **Rubric Review**: Verifier scores submission $0.88 > 0.70$ threshold.
4. **Challenge Window**: 24-hour challenge window passes without dispute.
5. **Settlement**: Bounty settles on-chain; 100 simulated credits transferred to contributor address.

---

## Step 5: Final Report & Audit Trail (§6.5, §16.8)
1. Argument graph updates dynamically with newly accepted evidence.
2. Final 10-section report exported with cryptographic hashes, Brier scores, and explicit human-review disclaimer.
