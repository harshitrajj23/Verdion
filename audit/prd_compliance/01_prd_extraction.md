# PRD Extraction & Complete Requirements Inventory
## VERIDION Decentralized Legal Intelligence Protocol

**Document Baseline**: `VERIDION_Product_Requirements_Document_v1.0.pdf`  
**Classification**: Master Requirements Baseline Extraction  
**Audit Phase**: PRD Compliance & Gap Analysis Audit (Phase 1 Deliverable)  
**Date**: 2026-10-31  

---

## 1. Executive Summary & Inventory Structure

This document establishes the exhaustive requirements baseline for VERIDION by extracting every functional, non-functional, security, data, agent/AI, smart contract, user interface, and acceptance criterion from the authoritative 28-page Product Requirements Document (`VERIDION_Product_Requirements_Document_v1.0.pdf`).

### Requirements Breakdown by Category

| Category | PRD Section | Identifier Scheme | Extracted Count |
| :--- | :--- | :--- | :---: |
| **Functional Requirements (FR)** | Section 7 (pp. 8–11) | `FR-001` to `FR-058` | **58** |
| **Non-Functional Requirements (NFR)** | Section 13.4, 18.2 (pp. 18, 23) | `PRD-NFR-001` to `PRD-NFR-012` | **12** |
| **Security & Trust Requirements (SEC)** | Section 17.1–17.5 (pp. 22–23) | `PRD-SEC-001` to `PRD-SEC-018` | **18** |
| **Data & Entity Requirements (DATA)** | Section 14, 14.1 (pp. 18–19) | `PRD-DATA-001` to `PRD-DATA-015` | **15** |
| **Agent & Reasoning Requirements (AGENT)** | Section 8, 9 (pp. 12–14) | `PRD-AGENT-001` to `PRD-AGENT-015` | **15** |
| **Smart Contract Requirements (SC)** | Section 12.1–12.5 (pp. 16–17) | `PRD-SC-001` to `PRD-SC-010` | **10** |
| **User Interface & UX Requirements (UI)** | Section 16.1–16.9 (pp. 20–21) | `PRD-UI-001` to `PRD-UI-010` | **10** |
| **Definition of Done (DoD)** | Appendix C (p. 28) | `PRD-DOD-001` to `PRD-DOD-011` | **11** |
| **TOTAL EXTRACTED REQUIREMENTS** | — | — | **139** |

---

## 2. Functional Requirements (FR-001 to FR-058)

### 2.1 Case Management (Section 7.1, p. 8)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-001` | P0 | §7.1 | Create a case with title, question, jurisdiction, date, facts, and optional document references. | Valid input creates a unique case ID and version. |
| `FR-002` | P0 | §7.1 | Validate scope and identify missing facts. | Missing required fields block analysis or create explicit questions. |
| `FR-003` | P0 | §7.1 | Version case scope and facts. | A material edit creates a new version; earlier outputs remain linked to their original version. |
| `FR-004` | P0 | §7.1 | Track lifecycle status. | UI accurately displays draft, retrieval, analysis, investigation, review, completed, and failed states. |
| `FR-005` | P1 | §7.1 | Export report. | Export includes source references, case version, and limitations. |

### 2.2 Legal Knowledge and Retrieval (Section 7.2, p. 9)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-006` | P0 | §7.2 | Use a curated, identifiable source collection. | Every included source has a stable identifier. |
| `FR-007` | P0 | §7.2 | Store source metadata. | Authority, jurisdiction, URL, retrieval time, and available publication/effective dates are recorded. |
| `FR-008` | P0 | §7.2 | Retrieve relevant passages. | Search returns passages with source IDs and references. |
| `FR-009` | P0 | §7.2 | Ground material claims. | Each material claim links to evidence or is explicitly marked unsupported. |
| `FR-010` | P0 | §7.2 | Respect effective dates where metadata permits. | Superseded material is flagged when known. |
| `FR-011` | P1 | §7.2 | Detect conflicting authority. | Potential conflict or applicability issue is surfaced. |
| `FR-012` | P0 | §7.2 | Treat retrieved content as untrusted data. | Instructions embedded in documents cannot override agent policies or tool permissions. |

### 2.3 Agent Orchestration and Argument Graph (Section 7.3, p. 9)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-013` | P0 | §7.3 | Support at least three specialized roles. | Research, interpretation, and adversarial roles execute end-to-end. |
| `FR-014` | P0 | §7.3 | Validate structured agent output. | Malformed output is rejected or retried within a bounded policy. |
| `FR-015` | P0 | §7.3 | Keep agent roles distinct. | Each output identifies role, claims, evidence, assumptions, uncertainties, and status. |
| `FR-016` | P0 | §7.3 | Apply bounded tool access. | Each agent can invoke only allowlisted tools. |
| `FR-017` | P0 | §7.3 | Handle failure and timeout. | Failures are visible and do not silently become successful conclusions. |
| `FR-018` | P1 | §7.3 | Record reproducibility metadata. | Model, prompt, tool, and source versions are captured where feasible. |
| `FR-019` | P0 | §7.3 | Represent claims as structured objects. | Claims have stable IDs and case/version links. |
| `FR-020` | P0 | §7.3 | Link claims to evidence. | Support, contradict, qualify, depend-on, and supersede edges are supported. |
| `FR-021` | P0 | §7.3 | Generate counterarguments. | Adversarial output includes testable objections and evidence references. |
| `FR-022` | P0 | §7.3 | Detect claim conflicts. | Incompatible claims or assumptions are flagged for review. |
| `FR-023` | P0 | §7.3 | Prioritize uncertainty. | Questions are ranked by impact, uncertainty, and research feasibility. |

### 2.4 Hybrid AI and Verification (Section 7.4, p. 10)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-024` | P0 | §7.4 | Use retrieval-grounded generation. | Agents receive relevant source passages and metadata. |
| `FR-025` | P0 | §7.4 | Run deterministic checks for encoded rules. | Known test cases return expected rule-engine outputs. |
| `FR-026` | P0 | §7.4 | Compute evidence digests. | The same canonical content yields the same digest. |
| `FR-027` | P0 | §7.4 | Evaluate forecasts against labels. | Scoring can be reproduced for a fixed dataset and scoring version. |
| `FR-028` | P0 | §7.4 | Do not rely solely on LLM confidence. | Reports identify evidence and empirical metrics separately from self-reported confidence. |
| `FR-029` | P0 | §7.4 | Support abstention and escalation. | Insufficient evidence can produce an unresolved result. |
| `FR-030` | P1 | §7.4 | Version evaluation configuration. | Dataset, rubric, model, and scoring versions are retained. |

### 2.5 Prediction Markets (Section 7.5, p. 10)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-031` | P0 | §7.5 | Define each event precisely. | Event, outcome, resolution source, deadline, scoring rules, challenge window, and void criteria are frozen. |
| `FR-032` | P0 | §7.5 | Accept probability forecasts. | Input validation rejects values outside [0,1]. |
| `FR-033` | P0 | §7.5 | Commit forecasts before deadline. | Late commitments revert. |
| `FR-034` | P0 | §7.5 | Verify reveal against commitment. | Incorrect probability, nonce, or market context is rejected. |
| `FR-035` | P0 | §7.5 | Aggregate forecasts deterministically off-chain. | Same eligible inputs and version yield the same aggregate. |
| `FR-036` | P0 | §7.5 | Display forecasts and disagreement. | UI labels aggregate, sample size, method, and market status. |
| `FR-037` | P0 | §7.5 | Close markets on time. | Closed markets reject new commitments and reveals outside their permitted windows. |
| `FR-038` | P0 | §7.5 | Resolve using predeclared rules. | Resolution references and authorized evaluator are recorded. |
| `FR-039` | P0 | §7.5 | Handle ambiguous outcomes. | Market can remain unresolved or be voided according to explicit rules. |

### 2.6 Evidence Bounty, Reputation, and Settlement (Section 7.6, p. 11)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-040` | P0 | §7.6 | Create a bounty with question, criteria, deadline, and reward. | Incomplete bounty cannot be opened. |
| `FR-041` | P0 | §7.6 | Use simulated credits for MVP. | No real-money wagering or unsupported token value is implied. |
| `FR-042` | P0 | §7.6 | Accept evidence with provenance. | Submission records source references, digest, contributor, and time. |
| `FR-043` | P0 | §7.6 | Publish review criteria. | Reviewer decisions cite the relevant criteria. |
| `FR-044` | P0 | §7.6 | Authorize reward release. | Only permitted resolution roles can settle. |
| `FR-045` | P1 | §7.6 | Detect duplicate evidence. | Likely duplicates are flagged for review. |
| `FR-046` | P0 | §7.6 | Support challenges. | Challenge must include a reason and arrive within the permitted window. |
| `FR-047` | P0 | §7.6 | Track agent performance. | History includes evaluated sample count and metrics. |
| `FR-048` | P0 | §7.6 | Use a proper scoring rule. | Brier score or documented alternative is tested against known examples. |
| `FR-049` | P0 | §7.6 | Guard against small-sample reputation inflation. | Low sample size is shown and cannot confer excessive weight. |
| `FR-050` | P0 | §7.6 | Update simulated credits deterministically. | Reward arithmetic is tested and auditable. |
| `FR-051` | P0 | §7.6 | Define missing and invalid reveal handling. | Rules are explicit and tested. |
| `FR-052` | P0 | §7.6 | Prevent duplicate settlement. | Repeated settlement attempts cannot release a second reward. |
| `FR-053` | P0 | §7.6 | Explain reputation changes. | UI shows the basis and event reference for changes. |

### 2.7 Audit and Reporting (Section 7.7, p. 11)

| ID | Priority | PRD Section | Exact Requirement Wording | PRD Acceptance Condition |
| :--- | :---: | :--- | :--- | :--- |
| `FR-054` | P0 | §7.7 | Record lifecycle events. | Case, market, bounty, challenge, resolution, and settlement events are available. |
| `FR-055` | P0 | §7.7 | Associate evidence versions with digests. | Digest verification detects changed content. |
| `FR-056` | P0 | §7.7 | Preserve decision provenance. | Report includes sources, claims, model/configuration versions, and unresolved questions. |
| `FR-057` | P0 | §7.7 | Expose transaction references. | Relevant contract events link to transaction hashes and explorer pages. |
| `FR-058` | P0 | §7.7 | Report limitations. | Verified facts, hypotheses, forecasts, and unresolved legal issues are visibly distinguished. |

---

## 3. Non-Functional Requirements (PRD-NFR-001 to PRD-NFR-012)

| ID | PRD Section | Target & Scope | PRD Requirement Description |
| :--- | :---: | :--- | :--- |
| `PRD-NFR-001` | §13.4 | Idempotency | Use idempotency keys for state-changing API requests. |
| `PRD-NFR-002` | §13.4 | State Clarity | Represent pending, confirmed, reverted, and failed blockchain transactions distinctly. |
| `PRD-NFR-003` | §13.4 | Fault Tolerance | Use bounded retries with backoff for transient errors. |
| `PRD-NFR-004` | §13.4 | Settlement Integrity | Never report settlement complete before confirmed chain state is observed. |
| `PRD-NFR-005` | §13.4 | Workflow Recovery | Persist workflow status so interrupted jobs can resume safely. |
| `PRD-NFR-006` | §13.4 | Server Authority | Do not use client-supplied scores or rewards as authoritative values. |
| `PRD-NFR-007` | §18.2 | Latency & Efficiency | Track and optimize time per assessment, research tasks, and time to resolve uncertainty. |
| `PRD-NFR-008` | §13.1, §20.2 | Cost Observability | Attach trace IDs to workflows; record token and API costs where available. |
| `PRD-NFR-009` | §18.2 | Reliability Metrics | Track timeout rate, invalid output rate, and successful recovery rate. |
| `PRD-NFR-010` | §18.2 | Chain Resilience | Track chain failure rate and ensure graceful reconciliation. |
| `PRD-NFR-011` | §13.1, §14.1 | Data Scalability | Scalable PostgreSQL storage for cases, claims, evidence passages, and audit events. |
| `PRD-NFR-012` | §3.3, §18.2 | Reproducibility | Fixed canonical input data and versioned rules must yield identical outputs and scoring. |

---

## 4. Security, Privacy, and Trust Requirements (PRD-SEC-001 to PRD-SEC-018)

| ID | PRD Section | Threat / Target | PRD Security Requirement & Mitigation |
| :--- | :---: | :--- | :--- |
| `PRD-SEC-001` | §7.2, §17.1 | Prompt Injection | Treat retrieved documents as untrusted data; isolate instructions using security fences; use allowlisted tools. |
| `PRD-SEC-002` | §8.1, §17.1 | Fabricated Citations | Verify retrieved source IDs and passage references; label ungrounded claims; do not invent citations. |
| `PRD-SEC-003` | §7.2, §17.1 | Outdated Authority | Store effective dates and source versions; flag unknown or superseded status. |
| `PRD-SEC-004` | §8.8, §17.1 | Agent Collusion | Track shared model providers and retrieval sources; avoid presenting agent count as independent evidence. |
| `PRD-SEC-005` | §10.4, §17.1 | Forecast Copying | Enforce commit-reveal pre-image privacy; canonical ABI encoding; strict deadline enforcement. |
| `PRD-SEC-006` | §11.4, §17.1 | Malicious Evidence | Implement digest checks and semantic duplicate detection; enforce reviewer rubric and challenge process. |
| `PRD-SEC-007` | §11.4, §17.1 | Sybil Identities | Apply rate limits, registration controls, and capped influence; recognize MVP limitations. |
| `PRD-SEC-008` | §11.4, §17.1 | Reviewer Collusion | Audit reviewer decisions; require conflict-of-interest disclosure; support independent review. |
| `PRD-SEC-009` | §10.4, §17.2 | Replay Attacks | Include `chainId`, `marketId`, `agentId`, and cryptographic `nonce` in commitment hashes. |
| `PRD-SEC-010` | §7.6, §17.2 | Duplicate Payouts | Ensure settlement idempotency and enforce explicit `SETTLED` state in smart contracts. |
| `PRD-SEC-011` | §12.4, §17.2 | Unauthorized Action | Restrict privileged functions and enforce explicit role checks (`evaluator`, `admin`). |
| `PRD-SEC-012` | §15.4, §17.1 | RPC / Indexer Faults | Reconcile pending/unknown states before retrying; handle RPC failures gracefully. |
| `PRD-SEC-013` | §12.3, §17.3 | Confidential Facts | Keep confidential legal documents, facts, and personal data off-chain in access-controlled storage. |
| `PRD-SEC-014` | §12.5, §17.3 | Secret Leakage | Never store private keys, complete API secrets, or passwords on-chain, in logs, or in git. |
| `PRD-SEC-015` | §17.2 | Emergency Controls | Include an emergency pause mechanism for critical incidents, with explicit auditability. |
| `PRD-SEC-016` | §17.2 | Arithmetic Bounds | Use checked arithmetic and bounded input values in contracts (e.g. Solidity 0.8+). |
| `PRD-SEC-017` | §17.4 | Human Oversight | Require qualified human review for high-impact decisions, conflicting authorities, or legal obligations. |
| `PRD-SEC-018` | §17.5 | Trust Disclosures | Explicitly document what is decentralized and what remains trusted (e.g., centralized evaluator). |

---

## 5. Data Model & Entity Requirements (PRD-DATA-001 to PRD-DATA-015)

| ID | PRD Section | Entity / Concept | Required Fields & Integrity Constraints |
| :--- | :---: | :--- | :--- |
| `PRD-DATA-001` | §14 | `Case` | `id`, `title`, `question`, `jurisdiction`, `assessment_date`, `facts`, `scope_version`, `status`, `created_at`. |
| `PRD-DATA-002` | §14 | `SourceDocument` | `id`, `title`, `authority`, `jurisdiction`, `URL`, `publication/effective dates`, `retrieved_at`, `digest`, `version`. |
| `PRD-DATA-003` | §14 | `EvidencePassage` | `id`, `document_id`, `passage_reference`, `content_reference`, `digest`, `source_version`. |
| `PRD-DATA-004` | §14 | `Agent` | `id`, `wallet_address`, `role`, `model/provider version`, `prompt version`, `status`, `reputation`. |
| `PRD-DATA-005` | §14 | `Claim` | `id`, `case_id`, `agent_id`, `claim_text`, `claim_type`, `assumptions`, `confidence metadata`, `timestamp`. |
| `PRD-DATA-006` | §14 | `ClaimEvidenceLink` | `claim_id`, `evidence_id`, `relationship`, `verification_status`. |
| `PRD-DATA-007` | §14 | `ArgumentEdge` | `source_claim_id`, `target_claim_id`, `relationship_type` (support/contradict/qualify/depend), `reason`, `timestamp`. |
| `PRD-DATA-008` | §14 | `PredictionMarket` | `id`, `case_id/version`, `question`, `outcome definition`, `resolution method`, `deadline`, `scoring version`, `status`, `contract`. |
| `PRD-DATA-009` | §14 | `Forecast` | `id`, `market_id`, `agent_id`, `probability`, `commitment hash`, `evidence digest`, `reveal status`, `transaction hashes`. |
| `PRD-DATA-010` | §14 | `EvidenceBounty` | `id`, `case_id`, `question`, `acceptance criteria`, `reward`, `deadline`, `status`, `contract reference`. |
| `PRD-DATA-011` | §14 | `EvidenceSubmission` | `id`, `bounty_id`, `contributor`, `digest`, `provenance`, `timestamp`, `review/challenge status`. |
| `PRD-DATA-012` | §14 | `Settlement` | `id`, `market/bounty`, `participant`, `score`, `reward`, `resolution reference`, `transaction hash`, `timestamp`. |
| `PRD-DATA-013` | §14 | `AuditEvent` | `id`, `case_id`, `event_type`, `actor`, `payload digest`, `transaction hash`, `timestamp`. |
| `PRD-DATA-014` | §14.1 | Timestamp & Key Integrity | Store timestamps in UTC; use stable IDs and foreign keys; record schema versions. |
| `PRD-DATA-015` | §3.3, §14.1 | Data Provenance | Maintain strict separation between operational records, demo fixtures, and synthetic test data. |

---

## 6. Agent and AI Architecture Requirements (PRD-AGENT-001 to PRD-AGENT-015)

| ID | PRD Section | Capability / Role | Exact PRD Specification |
| :--- | :---: | :--- | :--- |
| `PRD-AGENT-001` | §8.1 | Legal Researcher | Retrieve and organize relevant authority; output source references, extracted passages, candidate claims, and gaps; do not invent citations. |
| `PRD-AGENT-002` | §8.2 | Legal Interpreter | Map facts to potentially applicable requirements; identify rule elements, factual matches, assumptions, and exceptions. |
| `PRD-AGENT-003` | §8.3 | Adversarial Researcher | Challenge prevailing claims; search for contrary authority, missing facts, exceptions, and alternative interpretations. |
| `PRD-AGENT-004` | §8.4 | Evidence Verifier | Validate provenance and integrity; check source existence, metadata, duplicate material, and digest matches. |
| `PRD-AGENT-005` | §8.5 | Quantitative Forecaster | Forecast clearly defined outcomes; return probability, event definition, assumptions, and evidence digest; abstain when data is inadequate. |
| `PRD-AGENT-006` | §8.6 | Coordinator | Compare outputs, maintain argument graph, rank uncertainties, propose research tasks, and produce structured assessment. |
| `PRD-AGENT-007` | §8.7 | Agent Output Schema | Require 14 fields: `agent_id`, `role`, `case_id`, `case_version`, `claims[]`, `evidence_refs[]`, `assumptions[]`, `counterarguments[]`, `uncertainty`, `recommended_actions[]`, `model_version`, `prompt_version`, `tool_versions[]`, `status`, `error_details`. |
| `PRD-AGENT-008` | §8.8 | Independence Tracking | Track shared model providers, shared retrieval sources, and common upstream outputs; avoid presenting agent count as independent proof. |
| `PRD-AGENT-009` | §9.1 | Rule Engine Integration | Evaluate explicit, encoded legal requirements deterministically in combination with LLM retrieval. |
| `PRD-AGENT-010` | §9.1 | Argument Graph Tracking | Track claims, support, contradiction, assumptions, and dependencies in a structured graph. |
| `PRD-AGENT-011` | §9.2 | Forecast Aggregation | Compute unweighted mean: $p_{\text{agg}} = \frac{1}{N}\sum p_i$; support future weighted aggregation. |
| `PRD-AGENT-012` | §9.3 | Disagreement Metric | Compute variance $D = \frac{1}{N}\sum (p_i - \bar{p})^2$; trigger investigation on high disagreement. |
| `PRD-AGENT-013` | §9.4 | Uncertainty Ranking | Compute $\text{Priority}(q) = \text{Impact}(q) \times \text{Uncertainty}(q) \times \text{ResearchFeasibility}(q)$ with factors normalized to $[0,1]$. |
| `PRD-AGENT-014` | §9.5 | Brier Score Computation | Compute Brier proper score $\text{BS} = \frac{1}{N}\sum (p_i - y_i)^2, y_i \in \{0, 1\}$. |
| `PRD-AGENT-015` | §9.6 | Source-Grounding Policy | Every material legal claim must link to evidence or be marked unsupported; distinguish extracted text from interpretation. |

---

## 7. Smart Contract Requirements (PRD-SC-001 to PRD-SC-010)

| ID | PRD Section | Contract Module | PRD Requirements & Responsibilities |
| :--- | :---: | :--- | :--- |
| `PRD-SC-001` | §12.2 | `CaseRegistry.sol` | Register case/version identifiers and evidence digests; validate IDs; enforce access controls; no sensitive data on-chain. |
| `PRD-SC-002` | §12.2 | `AgentRegistry.sol` | Register agent address, role, and status; validate role authorizations; no identity claims. |
| `PRD-SC-003` | §12.2 | `PredictionMarket.sol` | Create market, accept commitments, verify reveals, track states (DRAFT to SETTLED); enforce deadlines and replay protection. |
| `PRD-SC-004` | §12.2 | `EvidenceBounty.sol` | Track bounty state (CREATED to SETTLED), simulated funding, submission digests, and reviewer decisions; prevent duplicate payout. |
| `PRD-SC-005` | §12.2 | `ReputationSettlement.sol`| Record authorized scores and simulated rewards; ensure settlement idempotency and checked arithmetic. |
| `PRD-SC-006` | §12.2 | `ChallengeResolution.sol`| Record challenges, deadlines, resolution references, and states (allow integrated implementation in Market/Bounty for MVP). |
| `PRD-SC-007` | §12.3 | On-Chain / Off-Chain Split | Keep private facts and full text off-chain; store only IDs, digests, commitments, and state transitions on-chain. |
| `PRD-SC-008` | §12.4 | Centralization Limits | Document authorized evaluator role; restrict privileged administrative calls; prepare for multisig controls. |
| `PRD-SC-009` | §13.1, §12.2 | EVM Testnet Deployment | Deploy contracts to EVM-compatible testnet (Sepolia); verify deployment addresses and configuration. |
| `PRD-SC-010` | §12.1 | Public Audit Events | Emit events for all state transitions, commitments, reveals, challenges, and settlements for off-chain indexing. |

---

## 8. User Interface Requirements (PRD-UI-001 to PRD-UI-010)

| ID | PRD Section | Screen / Area | PRD User Interface Specification |
| :--- | :---: | :--- | :--- |
| `PRD-UI-001` | §16.1 | Dashboard | Show active cases, cases needing research, open markets, active bounties, recent challenges, agent metrics, and settlements. Distinguish sample from live data. |
| `PRD-UI-002` | §16.2 | Case Workspace | Show question, jurisdiction, facts, source collection, agent activity, risk findings, argument graph, unresolved questions, and market/bounty links. |
| `PRD-UI-003` | §16.3 | Agent Laboratory | Show agent role, current task, sources consulted, claims, counterarguments, forecast, uncertainty, elapsed time, cost, and failures. |
| `PRD-UI-004` | §16.4 | Argument Graph Explorer | Select claim and inspect evidence, source passage, agent, assumptions, edges, and verification state; provide text/table fallback. |
| `PRD-UI-005` | §16.5 | Market Page | Show event, resolution rules, aggregate probability, individual revealed forecasts, sample size, disagreement metric, deadlines, and settlement. |
| `PRD-UI-006` | §16.6 | Bounty Page | Show research question, rubric, simulated reward, deadline, submissions, source metadata, review reasoning, challenges, and settlement. |
| `PRD-UI-007` | §16.7 | Audit Explorer | Show contract addresses, network, transaction hashes, commitment/reveal events, evidence digests, challenges, and reputation updates. |
| `PRD-UI-008` | §16.8 | Final Report Generator | Generate report covering 10 required sections: executive summary, facts, sources, claims, counterarguments, risk findings, forecasts, uncertainties, next steps, audit references. |
| `PRD-UI-009` | §16.9 | Accessibility & States | Provide loading, empty, failed, and partial-result states; use text labels in addition to color; display timestamps unambiguously. |
| `PRD-UI-010` | §16.9 | Transaction Integrity | Explain wallet/network requirements; show pending and confirmed chain states distinctly; never fabricate transaction hashes. |

---

## 9. Definition of Done (PRD-DOD-001 to PRD-DOD-011)

| ID | PRD Section | Criterion | Exact PRD Definition of Done Text |
| :--- | :---: | :--- | :--- |
| `PRD-DOD-001` | Appendix C | Scoped Case Versioning | One scoped case can be created and versioned. |
| `PRD-DOD-002` | Appendix C | Multi-Agent Execution | At least three agent roles produce structured, evidence-linked outputs. |
| `PRD-DOD-003` | Appendix C | Argument Graph | Argument graph exposes support and contradiction relationships. |
| `PRD-DOD-004` | Appendix C | Hybrid AI & Abstention | Hybrid checks and abstention are operational. |
| `PRD-DOD-005` | Appendix C | Market Lifecycle | A market can be created, committed to, revealed, resolved or voided, and settled under explicit rules. |
| `PRD-DOD-006` | Appendix C | Bounty Lifecycle | A bounty can be opened, submitted to, challenged, and settled using simulated credits. |
| `PRD-DOD-007` | Appendix C | Contract Invariants | Contracts enforce access control, deadlines, and duplicate-settlement prevention. |
| `PRD-DOD-008` | Appendix C | Audit & References | Audit events and transaction references are visible. |
| `PRD-DOD-009` | Appendix C | Baseline Comparison | Evaluation compares at least one single-agent baseline and one multi-agent baseline. |
| `PRD-DOD-010` | Appendix C | Limitations Documented | Known limitations, trust assumptions, and security risks are documented. |
| `PRD-DOD-011` | Appendix C | Repeatable Demo | The end-to-end demo is repeatable and does not rely on fabricated live results. |

---

## 10. Traceability & Audit Baseline Sign-off

The 139 requirements extracted above constitute the authoritative, immutable baseline against which the remainder of this PRD compliance audit is conducted. No requirements have been altered, softened, or omitted.

