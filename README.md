# VERIDION — Decentralized Legal Intelligence Protocol

> **Reason. Predict. Verify.**  
> *A decentralized protocol coordinating specialized AI agents to research legal and regulatory questions, create competing evidence-backed arguments, forecast precisely defined outcomes, and resolve uncertainties on-chain.*

---

## 1. System Architecture & Repository Layout

```
verdion/
├── shared/                         # Track 1: Shared Schemas, Canonical Digest & Protocol Specs
│   ├── schemas/                    # Frozen JSON Schemas (§20.1, §8.7)
│   │   ├── case.schema.json        # FR-001..FR-004
│   │   ├── claim.schema.json       # FR-019..FR-022
│   │   ├── evidence.schema.json    # FR-006..FR-010, FR-026
│   │   ├── forecast.schema.json    # FR-031..FR-035, §10.4
│   │   ├── bounty.schema.json      # FR-040..FR-046, §11
│   │   ├── settlement.schema.json  # FR-048..FR-053
│   │   └── agent_output.schema.json# §8.7 schema (6 agents)
│   ├── src/
│   │   ├── canonicalDigest.ts      # Canonical JSON digest & ABI commitment hash (FR-026, §10.4)
│   │   └── canonicalDigest.py      # Python cryptographic parity engine
│   ├── rubrics/
│   │   ├── bounty_acceptance.json  # §11.3 6-criterion evaluation rubric
│   │   └── market_resolution.json  # §10.5 resolution and voiding rules
│   ├── threat_model.md             # §17.1 & §17.2 threat matrix and mitigations
│   └── demo_script.md              # PRD Appendix A end-to-end demo walkthrough
│
├── contracts/                      # Track 2: Solidity Contracts & Foundry Test Suite (§12)
│   ├── foundry.toml                # Foundry configuration
│   ├── src/
│   │   ├── CaseRegistry.sol        # Versioned scope & evidence anchoring (FR-001..004)
│   │   ├── AgentRegistry.sol       # Agent role checks & status (PRD §8)
│   │   ├── PredictionMarket.sol    # Commit-reveal H(chainId, mId, aId, p, digest, nonce), challenge & settlement
│   │   ├── EvidenceBounty.sol      # Bounty funding, submission digests, rubric review & challenge
│   │   └── ReputationSettlement.sol# Simulated credits, Brier proper scoring, idempotent settlement
│   ├── test/
│   │   └── VerdionTest.t.sol       # Happy path, expiry, mismatch rejection, duplicate settlement rejection
│   └── script/
│       └── Deploy.s.sol            # Testnet deployment script
│
├── ml/                             # Track 3: ML/AI & Hybrid Reasoning Engine (§8, §9, §18)
│   ├── corpus/                     # Curated European Union regulatory corpus (FR-006, FR-007)
│   │   ├── corpus_metadata.json    # Sources, authorities, effective dates
│   │   └── passages.json           # Passages with stable IDs and keywords
│   ├── retrieval/
│   │   ├── isolation.py            # Prompt-injection isolation security fence (FR-012, TH-01)
│   │   └── retriever.py            # Passage search, provenance tracking & digest calculation
│   ├── rules/
│   │   ├── engine.py               # Deterministic legal rule engine (FR-025, §9.1)
│   │   └── test_rules.py           # Unit tests for rule evaluations
│   ├── argument_graph/
│   │   └── graph.py                # Graph nodes, typed edges (support, contradict, qualify, depend, supersede)
│   ├── uncertainty/
│   │   └── priority.py             # Priority = Impact × Uncertainty × Feasibility (FR-023, §9.4)
│   ├── aggregation/
│   │   └── scoring.py              # Unweighted mean, disagreement variance, Brier score (§9.2, §9.3, §9.5)
│   ├── agents/
│   │   └── agent_swarm.py          # 6 Agents: Researcher, Interpreter, Adversarial, Verifier, Forecaster, Coordinator
│   └── benchmark/                  # 20 Scenarios with held-out split (§18.1, §18.3)
│       ├── scenarios.json          # 14 train / 6 held-out test scenarios
│       ├── evaluate.py             # Evaluates Baselines A, B, C vs VERIDION
│       └── results.json            # Empirical benchmark results
│
├── frontend/                       # Track 4: Next.js + React + TypeScript + Tailwind UI (§16)
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx          # Root theme, headers, store context, toasts
│   │   │   ├── page.tsx            # Dashboard (§16.1): Sample vs Live toggle, metrics, spotlight
│   │   │   ├── cases/page.tsx      # Case Workspace (§16.2): Scope, facts, sources, timeline
│   │   │   ├── agents/page.tsx     # Agent Laboratory (§16.3): Telemetry, cost, latency, failures
│   │   │   ├── graph/page.tsx      # Argument Graph Explorer (§16.4): Visual SVG + accessible table fallback
│   │   │   ├── markets/page.tsx    # Prediction Markets (§16.5): Commit-reveal terminal & scoring
│   │   │   ├── bounties/page.tsx   # Evidence Bounties (§16.6): Submissions, rubric, challenge
│   │   │   ├── audit/page.tsx      # Audit Explorer (§16.7): Contract registry & tx proofs
│   │   │   ├── report/page.tsx     # Final Report (§16.8): 10-section report & Markdown/JSON/PDF export
│   │   │   └── benchmark/page.tsx  # Benchmark & Baselines Viewer (§18.1, §18.2)
│   │   ├── components/
│   │   │   ├── AppHeader.tsx       # Brand, Network, Simulated credit faucet, Wallet connect (§16.9)
│   │   │   ├── AppSidebar.tsx      # Navigation with PRD section tags
│   │   │   ├── LiveOrSampleBadge.tsx # Toggle between Curated Benchmark Data and Live Chain Data
│   │   │   ├── ArgumentGraph.tsx   # Interactive SVG canvas + accessible text table fallback
│   │   │   ├── AgentCard.tsx       # Agent role telemetry card
│   │   │   └── ToastContainer.tsx  # Pending / confirmed / reverted tx toasts
│   │   └── lib/
│   │       ├── store.ts            # State management, mutations, and Web3 hooks
│   │       └── mockData.ts         # PRD Appendix A comprehensive dataset
│   ├── tailwind.config.js          # Sleek glassmorphic dark palette (emerald, cyan, rose, amber)
│   └── package.json
│
└── backend/                        # Track 5: FastAPI Reasoning, Data & API Server
    ├── app/
    │   ├── api/v1/                 # Endpoints: cases, markets, bounties, agents, evaluations
    │   ├── core/                   # Config, database, crypto, middleware, error handling
    │   ├── models/                 # SQLAlchemy async ORM entities
    │   ├── schemas/                # Pydantic validation schemas
    │   └── services/               # Rule engine, agent swarm, argument graph, evaluation
    ├── tests/                      # Automated pytest suite (17 tests)
    └── requirements.txt            # Python dependencies
```

---

## 2. Quickstart & Verification Commands

### A. Run Deterministic Rule Engine Tests (Python)
```bash
python3 -m unittest ml/rules/test_rules.py
```

### B. Run Benchmark Evaluation (20 Scenarios across Baselines A, B, C & VERIDION)
```bash
python3 ml/benchmark/evaluate.py
```

### C. Run Foundry Smart Contract Tests
```bash
cd contracts
forge test -vvv
```

### D. Start Next.js Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to interact with the full VERIDION dashboard.

---

## 3. Backend (FastAPI Reasoning & API Server)

The `backend/` directory provides a high-performance asynchronous API server powering protocol case management, deterministic legal rule checks, multi-agent reasoning, argument graph synthesis, prediction markets, and evidence bounties.

### A. Start the Backend API Server
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive OpenAPI documentation is available at: `http://127.0.0.1:8000/api/v1/docs`

### B. Run Backend Test Suite
```bash
pytest backend/tests -v
```

### C. Backend API Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/cases` | Create a case with scope validation and version tracking |
| `GET` | `/api/v1/cases/{id}` | Retrieve case details, facts, and scope status |
| `PATCH` | `/api/v1/cases/{id}` | Update case facts and increment scope version |
| `POST` | `/api/v1/cases/{id}/analyze` | Execute multi-agent analysis & hybrid legal rule checks |
| `GET` | `/api/v1/cases/{id}/analysis` | Retrieve structured argument graph, claims, and conflicts |
| `GET` | `/api/v1/cases/{id}/report` | Generate complete 10-section compliance audit report |
| `POST` | `/api/v1/markets` | Create prediction market for verifiable benchmark outcome |
| `POST` | `/api/v1/markets/{id}/commit` | Commit forecast hash `keccak256(...)` |
| `POST` | `/api/v1/markets/{id}/reveal` | Reveal forecast with secret nonce and probability |
| `POST` | `/api/v1/markets/{id}/settle` | Settle market, compute Brier scores, and award credits |
| `POST` | `/api/v1/bounties` | Create targeted research evidence bounty |
| `POST` | `/api/v1/bounties/{id}/submissions` | Submit evidence passage with canonical digest |
| `GET` | `/api/v1/agents` | List protocol agents, roles, and reputation metrics |
| `GET` | `/api/v1/evaluations/run` | Run 20-scenario benchmark evaluation (Baselines vs VERIDION) |
