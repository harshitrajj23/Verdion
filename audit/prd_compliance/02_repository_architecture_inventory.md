# Repository Architecture Inventory
## VERIDION Decentralized Legal Intelligence Protocol

**Audit Phase**: PRD Compliance & Gap Analysis Audit (Phase 2 Deliverable)  
**Date**: 2026-10-31  
**Repository Branch**: `Divyank`  
**Git Base**: `Verdion/`  

---

## 1. System Overview & Architectural Topology

VERIDION is architected as an **Auditable Regulatory Decision Infrastructure (Option C)**, coordinating multi-agent legal reasoning, deterministic rule verification, commit-reveal prediction markets, evidence bounties, and zero-trust cryptographic audit chains.

```
                     ┌────────────────────────────────────────┐
                     │          Next.js 14 Frontend           │
                     │  (App Router, Tailwind, Viem, Lucide)  │
                     └───────────────────┬────────────────────┘
                                         │ HTTP REST / JSON API
                     ┌───────────────────▼────────────────────┐
                     │        FastAPI Backend Core            │
                     │  (10 Routers, Pydantic v2, CORS/Auth)  │
                     └─┬─────────┬───────────┬──────────────┬─┘
                       │         │           │              │
      ┌────────────────▼─┐   ┌───▼────────┐  │  ┌───────────▼───────────┐
      │ Multi-Agent Swarm│   │ Ingestion  │  │  │ Smart Contract Engine │
      │ 6 Agent Roles    │   │ Adapters   │  │  │ 5 Solidity Contracts  │
      │ Rule Engine      │   │ EUR-Lex    │  │  │ Sepolia (Chain 11155111)│
      │ Argument Graph   │   │ Curia/CJEU │  │  │ Web3 / Viem / RPC     │
      │ HuggingFace/Local│   │ EDPB PDF   │  │  └───────────────────────┘
      └──────────────────┘   └────────────┘  │
                                             │
      ┌──────────────────────────────────────▼──────────────────────────┐
      │ Cryptographic Audit & Verification Layer                        │
      │ • Canonical Decision Serialization (VCP-1 Standard)             │
      │ • Zero-Trust Standalone Offline Verifier (SHA-256 + Merkle)     │
      │ • EVM-Packed Keccak-256 Commit-Reveal Engine                    │
      │ • SQLite / PostgreSQL Relational Database (17 Tables)           │
      └─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Inventory Table

| Component | Repository Location | Core Responsibility | Dependencies | Entry Point | Relevant Tests | Integration Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Case Router & API** | `backend/app/api/v1/cases.py` | Case CRUD, scope validation, multi-agent analysis trigger, decision record export, unified workspace | `CaseService`, `WorkflowService`, `DecisionService` | REST: `/api/v1/cases` | `test_cases_and_agents.py`, `test_phase5e_workflow.py` | **Integrated** |
| **Ingestion Router & API** | `backend/app/api/v1/ingestion.py` | Official source trigger, automated passage extraction, ingestion job inspection, re-analysis proposals | `IngestionService` | REST: `/api/v1/ingestion` | `test_phase5b_adapters.py` | **Integrated** |
| **Audit Router & API** | `backend/app/api/v1/audit.py` | Immutable event journal, hash chain query, offline package verification endpoint | `AuditService`, `IndependentAuditVerifier` | REST: `/api/v1/audit` | `test_end_to_end.py`, `test_phase5c_option_c.py` | **Integrated** |
| **Markets Router & API** | `backend/app/api/v1/markets.py` | Prediction market creation, commitment submission, reveal verification, settlement, Brier evaluation | `MarketService`, `BlockchainService` | REST: `/api/v1/markets` | `test_markets_and_bounties.py`, `test_phase5f_benchmarks.py` | **Integrated** |
| **Bounties Router & API**| `backend/app/api/v1/bounties.py` | Evidence bounty creation, submission ingest, challenge filing, authorized reward settlement | `BountyService`, `BlockchainService` | REST: `/api/v1/bounties` | `test_markets_and_bounties.py` | **Integrated** |
| **Agents Router & API** | `backend/app/api/v1/agents.py` | Agent metric inspection, reputation scores, individual role executions | `AgentService` | REST: `/api/v1/agents` | `test_cases_and_agents.py` | **Integrated** |
| **Integrations Router** | `backend/app/api/v1/integrations.py`| Sepolia contract deployment status, read-only on-chain verification, transaction checks | `BlockchainService`, `web3` | REST: `/api/v1/integrations`| `test_phase5e_workflow.py` | **Integrated** |
| **Workflow Service** | `backend/app/services/workflow_service.py`| Option C 12-state decision lifecycle orchestrator; atomic state machine transitions | `CaseService`, `DecisionService`, `IndependentAuditVerifier`| Python Service Class | `test_phase5e_workflow.py`, `test_phase5f_benchmarks.py` | **Integrated** |
| **Decision Service** | `backend/app/services/decision_service.py`| Canonical VCP-1 decision record builder, audit package assembler | `canonical.py`, `entities.py`, `AuditService` | Python Service Class | `test_phase5c_option_c.py`, `test_phase5d_adversarial.py` | **Integrated** |
| **Independent Verifier**| `backend/app/services/audit_verifier.py` | Zero-trust offline auditor; recomputes canonical digests, passage hashes, Merkle checkpoints, commitments | `canonical.py`, `crypto.py`, `eth_abi` | CLI / Python Service Class | `test_phase5c_option_c.py`, `test_phase5d_adversarial.py` | **Integrated** |
| **EUR-Lex Adapter** | `backend/app/services/ingestion/eur_lex_adapter.py`| Fetches official EU directives/regulations from EUR-Lex Cellar/REST; XML Formex segmentation | `httpx`, `base_adapter.py` | Service / Ingestion Trigger | `test_phase5b_adapters.py` | **Integrated** |
| **CJEU Curia Adapter** | `backend/app/services/ingestion/cjeu_adapter.py` | Scrapes Court of Justice (CJEU) case judgments via Curia search engine; extracts grounds & rulings | `httpx`, `BeautifulSoup4` | Service / Ingestion Trigger | `test_phase5b_adapters.py` | **Integrated** |
| **EDPB Guidelines Adapter**| `backend/app/services/ingestion/edpb_adapter.py` | Downloads official EDPB regulatory guidance PDFs; extracts text with `pdfplumber` and character offsets | `httpx`, `pdfplumber` | Service / Ingestion Trigger | `test_phase5b_adapters.py` | **Integrated** |
| **Deterministic Rule Engine** | `backend/app/services/rule_engine.py` / `ml/rules/engine.py` | Evaluates codified statutory requirements (GDPR Art 5, 6, 9, 13, 17, 89; AI Act risk tiers) | Pure Python / Relational Logic | Python Class | `test_rule_engine.py` | **Integrated** |
| **Agent Swarm Service** | `backend/app/services/agent_service.py` | Coordinates 6 agent roles (Researcher, Interpreter, Adversary, Verifier, Forecaster, Coordinator) | `HuggingFaceInferenceService`, `RuleEngine` | Python Service Class | `test_cases_and_agents.py` | **Integrated** |
| **HF Inference Service**| `backend/app/services/hf_service.py` | Connects to local vLLM/Ollama OpenAI-compatible endpoint or Hugging Face Hub; falls back to rules | `httpx`, `settings` | Python Class | `test_cases_and_agents.py` | **Integrated** |
| **Canonical Serializer**| `backend/app/core/canonical.py` | RFC 8785 JSON canonicalizer; deterministic float rounding, Unicode NFC normalization, SHA-256 | `json`, `unicodedata`, `hashlib` | Python Core Module | `test_crypto.py`, `test_phase5c_option_c.py` | **Integrated** |
| **Crypto Utilities** | `backend/app/core/crypto.py` | Keccak-256, EVM packed encoding, Brier score calculation, variance calculation, nonce generator | `web3`, `eth_abi`, `eth_utils` | Python Core Module | `test_crypto.py` | **Integrated** |
| **Entities & Database**| `backend/app/models/entities.py` | SQLAlchemy async ORM definitions for all 17 tables | `sqlalchemy`, `aiosqlite` / `asyncpg` | DB Connection / Migrations | `test_cases_and_agents.py`, `test_end_to_end.py` | **Integrated** |
| **CaseRegistry Contract** | `contracts/src/CaseRegistry.sol` | On-chain registration of case scope hashes, evidence digests, and version updates | Foundry / Solidity 0.8.20 | EVM: `0xF1bA...819e` | `VerdionTest.t.sol` | **Deployed (Sepolia)** |
| **AgentRegistry Contract**| `contracts/src/AgentRegistry.sol`| On-chain agent registration and role check authorizations | Foundry / Solidity 0.8.20 | EVM: `0x42e0...b9ad` | `VerdionTest.t.sol` | **Deployed (Sepolia)** |
| **PredictionMarket Contract** | `contracts/src/PredictionMarket.sol` | Commit-reveal forecast recording, deadline validation, challenge window enforcement | Foundry / Solidity 0.8.20 | EVM: `0xFF5e...EE27` | `VerdionTest.t.sol` | **Deployed (Sepolia)** |
| **EvidenceBounty Contract** | `contracts/src/EvidenceBounty.sol` | Bounty funding, submission hashes, reviewer settlement, duplicate payout prevention | Foundry / Solidity 0.8.20 | EVM: `0x5d47...e58C` | `VerdionTest.t.sol` | **Deployed (Sepolia)** |
| **ReputationSettlement Contract** | `contracts/src/ReputationSettlement.sol` | Idempotent scoring records and reward credit balance accounting | Foundry / Solidity 0.8.20 | EVM: `0x643c...4aA3` | `VerdionTest.t.sol` | **Deployed (Sepolia)** |
| **Frontend Workspace** | `frontend/src/app/cases/page.tsx` | Comprehensive 6-area Option C Decision Workspace (Overview, Evidence, Record, Forecasts, Verifier, History) | React, Next.js 14, Lucide | Route: `/cases` | `npm run build` | **Integrated** |
| **Frontend Audit Explorer**| `frontend/src/app/audit/page.tsx` | Contract registry display, chronological event journal, offline audit package import/verify | React, Next.js 14, Lucide | Route: `/audit` | `npm run build` | **Integrated** |
| **Frontend Markets** | `frontend/src/app/markets/page.tsx` | Prediction market terminal; commit-reveal status, consensus aggregation, timeline deadlines | React, Next.js 14, Lucide | Route: `/markets` | `npm run build` | **Integrated** |
| **Frontend Bounties** | `frontend/src/app/bounties/page.tsx`| Evidence bounty board; submission form, acceptance rubric, reward pool display | React, Next.js 14, Lucide | Route: `/bounties` | `npm run build` | **Integrated** |
| **Frontend Benchmark** | `frontend/src/app/benchmark/page.tsx`| Empirical evaluation charts, Brier scoring, baseline comparisons, discrimination checks | React, Recharts | Route: `/benchmark` | `benchmarkPage.test.tsx` | **Integrated** |
| **Frontend Sources** | `frontend/src/app/sources/page.tsx` | Legal corpus manager, live ingestion triggers for EUR-Lex/Curia/EDPB, passage viewer | React, Next.js 14, Lucide | Route: `/sources` | `npm run build` | **Integrated** |

---

## 3. Detailed Subsystem Analysis

### 3.1 Backend & API Subsystem
- **Framework**: FastAPI with asynchronous endpoints (`async def`) and dependency injection for database sessions (`get_db`).
- **Validation**: Strict Pydantic v2 schemas across all requests and responses (`CaseCreateRequest`, `MarketCommitRequest`, `DecisionRecord`, `AuditPackage`).
- **Data Integrity**: Idempotency keys supported on critical state transitions (`/workflow/transition`).
- **Error Handling**: Custom exception hierarchy mapped to HTTP status codes (`InvalidScopeException` -> 400, `CommitmentMismatchException` -> 422, `UnauthorizedResolutionException` -> 403, `MarketClosedException` -> 409).

### 3.2 Ingestion & Legal Corpus Subsystem
- **Multi-Source Support**: Three production adapters implemented in `backend/app/services/ingestion/`:
  1. `EURLexAdapter`: Queries EUR-Lex CELLAR SPARQL / REST API; parses Formex XML structure.
  2. `CJEUAdapter`: Scrapes Curia judgments, extracting title, case number, legal grounds, and operative ruling.
  3. `EDPBAdapter`: Retrieves official PDF guidelines; segments text into passages with byte/character offsets.
- **Idempotent Caching**: Content digest lookup ensures identical source documents are not duplicated in the database (measured at $7.8\,\mu\text{s}$ cache retrieval in Phase 5F).
- **Provenance Partitioning**: Distinguishes `REMOTE_OFFICIAL_SOURCE` from `BUNDLED_FIXTURE` and `SYNTHETIC_TEST`.

### 3.3 Hybrid AI & Agent Swarm Subsystem
- **Agent Roles**: 6 distinct agents defined in `backend/app/services/agent_service.py`:
  - `agent_legal_researcher`: Ingests passages and generates statutory grounding claims.
  - `agent_legal_interpreter`: Maps case facts against statutory requirements using the deterministic rule engine.
  - `agent_adversarial_researcher`: Evaluates counterarguments, statutory defenses (e.g. GDPR Art 6(1)(f)), and exceptions.
  - `agent_evidence_verifier`: Validates that every claim citation matches an on-disk evidence passage digest.
  - `agent_quantitative_forecaster`: Computes calibrated probabilities, nonces, and commitment pre-images.
  - `agent_coordinator`: Synthesizes argument graph edges (`SUPPORTS`, `CONTRADICTS`), ranks uncertainties, and seals the decision.
- **Inference Mode**: Dual-mode execution:
  - Mode 1: Local / Hugging Face model inference via `HuggingFaceInferenceService` (supports vLLM/Ollama/TGI).
  - Mode 2: Deterministic statutory rule engine fallback when offline (ensuring 100% reproducible execution).

### 3.4 Cryptographic Audit & Verifier Subsystem
- **VCP-1 Standard**: Veridion Commitment Protocol packing:
  $$\text{Commitment} = \text{keccak256}(\text{abi.encodePacked}(\text{chainId}, \text{marketBytes}, \text{walletAddress}, \text{probBps}, \text{digestBytes}, \text{nonceBytes}))$$
- **Sequential Hash Chaining**: Every `AuditEvent` links to its predecessor via `parent_hash`, building an unbroken audit ledger.
- **Merkle Tree Checkpoints**: Periodic checkpoints computed via `compute_local_merkle_root` (supporting RFC 6962 leaf hashing).
- **Standalone Verification**: `IndependentAuditVerifier` executes completely decoupled from backend databases and external networks.

### 3.5 Smart Contract & Blockchain Subsystem
- **Solidity Version**: `^0.8.20` with checked arithmetic and custom error types.
- **Contracts Deployed to Sepolia Testnet**:
  - `CaseRegistry`: `0xF1bA6945a6c3822292f750b2848c40C39D55819e`
  - `AgentRegistry`: `0x42e05739E053725F7f3e8b0726B5f0962803b9ad`
  - `PredictionMarket`: `0xFF5e85547E443e3d50b393E09885c6Eb9671EE27`
  - `EvidenceBounty`: `0x5d47e805565A98517A74a95aF9608149A977e58C`
  - `ReputationSettlement`: `0x643c7B6022e0329b3Bff73e660ebEcb7729F4aA3`
- **Execution Separation**: In operational runtime, local transactions run in `LOCAL_SIMULATION` mode to avoid non-deterministic testnet gas delays and funds depletion, while preserving bit-for-bit EVM parity.

### 3.6 Frontend User Interface Subsystem
- **Architecture**: Next.js 14 App Router, TypeScript, React 18, Tailwind CSS, Lucide Icons, and Recharts.
- **Unified Decision Workspace**: Evolved in Phase 5G into a 6-area layout:
  - Area A: Decision Overview (Metadata, Jurisdiction, Trust Architecture Status, Missing Facts)
  - Area B: Evidence Explorer (Passage search, byte offsets, source provenance, recomputable digests)
  - Area C: Decision Record (VCP-1 canonical serialization, grounded claims table, JSON export)
  - Area D: Forecasting & Commitments (Commit-reveal deadlines, consensus probabilities, $N=0$ disclosure)
  - Area E: Verification Center (Zero-trust offline audit check, disposable copy tamper demonstration)
  - Area F: Audit History (Merkle checkpoints, chronological hash-chained event journal)

---

## 4. Architectural Gaps, Dead Code, and Implementation Boundaries

### 4.1 Foundry Local CLI Dependency Boundary
- **Finding**: `forge` CLI is not installed on the local Windows PATH environment.
- **Impact**: Foundry contract test suites (`contracts/test/*.t.sol`) cannot be executed locally via command line.
- **Mitigation / Reality**: Contract verification is established via Sepolia deployment receipts, bytecode inspection, web3 RPC call verification, and Python-to-Solidity cross-language parity vectors in `test_crypto.py` and `test_phase5f_benchmarks.py`.

### 4.2 LLM Live Inference vs Deterministic Rules Boundary
- **Finding**: When no external GPU server or local Ollama daemon is actively running, `HuggingFaceInferenceService` falls back to the internal `DeterministicRuleEngine`.
- **Impact**: Text output from agents is generated deterministically from rule templates rather than open-ended natural language.
- **Compliance Status**: This behavior is explicitly compliant with PRD Section 7.4 (`FR-025`), Section 9.1, and Option C principles.

### 4.3 Operational Court Cases Sample Size Boundary ($N = 0$)
- **Finding**: In `veridion.db`, while 43 prediction markets exist and 125 forecasts have been submitted, the sample size of genuine resolved external court cases (e.g. CJEU final rulings) is $N = 0$.
- **Impact**: Real-world judicial calibration cannot be claimed empirically.
- **Compliance Status**: Fully disclosed across all audit reports and the frontend UI, strictly complying with PRD Section 1.4, 7.6 (`FR-049`), and 18.2.

### 4.4 Disconnected or Orphaned Modules
- `ml/benchmark/invalid_hardcoded/`: Contains historical artifacts from Phase 1 audit where hardcoded responses were isolated. Retained for historical regression comparison; excluded from production imports.
- `scripts/migrate_audit_chain.py`: One-time schema migration script for audit event parent hashes; not part of the active production API.

