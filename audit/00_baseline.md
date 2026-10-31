# VERIDION Audit — Phase 0: Repository Baseline & Runtime State

**Audit Timestamp**: 2026-10-27T04:10:00+05:30  
**Lead Auditor**: Principal Software Architect & QA Automation Lead  
**Requirements Reference**: `VERIDION_Product_Requirements_Document_v1.0.pdf`  
**Audited Target**: VERIDION Protocol Codebase  
**Deliverable**: `audit/00_baseline.md`  

---

## 1. Repository Identification & Version Control

| Dimension | Measured / Observed Value | Evidence Command / Source |
|---|---|---|
| **Local Workspace Root** | `C:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion` | Antigravity IDE Workspace URI |
| **Git Repository Root** | `C:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion` | `git rev-parse --show-toplevel` |
| **Active Branch** | `Divyank` | `git branch --show-current` |
| **Audited Commit SHA** | `ca33ac221ed5492fcd47c21874fb111f655734a3` | `git rev-parse HEAD` |
| **Latest Commit Message** | `fix(frontend): wire Sepolia deployments, lifecycle receipts, and transparency disclosures` | `git log -1 --pretty=%B` |
| **Commit Author / Date** | Harshit Raj (`hr9199274@gmail.com`) / Mon Oct 26 23:24:55 2026 +0530 | `git log -1 --format="%an <%ae> %ad"` |
| **Remote Origin URL** | `https://github.com/harshitrajj23/Verdion.git` | `git remote -v` |
| **Remote HEAD Ref** | `refs/heads/main` -> `ca33ac221ed5492fcd47c21874fb111f655734a3` | `git ls-remote origin HEAD` |
| **Tracking Status** | Up to date with `origin/main` (ahead 22 vs older `origin/Divyank`) | `git status --short --branch` |
| **Working Tree Status** | **Clean** (0 uncommitted modifications, 0 untracked files) | `git status -uall` |

### Recent Git Commit History (Chronological Trajectory)
```text
* ca33ac2 (HEAD -> Divyank, origin/main, origin/HEAD, main) fix(frontend): wire Sepolia deployments, lifecycle receipts, and transparency disclosures
* 2852144 Merge integrate/backend-divyank: backend, Sepolia deployment, frontend theme
* 5e6d45a fix(backend): match settlement receipt by market id only
* 5c02bb1 feat(frontend): apply theme styling to markets, bounties, audit, report, and benchmark pages
* 480efef feat(frontend): apply theme styling to dashboard, cases, agents, and graph pages
* f36d79d feat(frontend): apply cream-lavender apple theme layout, components, styles, and tailwind config
* d334473 test(contracts): add testCommitmentHashVector31337 vector test
* d175f09 fix(backend): lookup stored confirmed settlement receipt instead of hardcoded null
* 4ae8ae0 fix(backend): remove agent-id address fallback and synthetic settlement hash
* 03b90ad feat(ml): complete relevance review sample annotations and record held-out freeze decision
```

---

## 2. Execution Environment & Runtimes

| Runtime / Engine | Version Detected | Location |
|---|---|---|
| **Operating System** | Windows 11 Enterprise (win32, x64) | PowerShell `[System.Environment]::OSVersion` |
| **Python** | `Python 3.11.9` | `Verdion\.venv\Scripts\python.exe` |
| **Node.js** | `v24.14.0` | `node -v` |
| **npm** | `11.9.0` | `npm -v` |
| **Pytest** | `pytest 9.1.1` | `pytest --version` |
| **Solidity Compiler Target** | `^0.8.20` | `contracts/foundry.toml`, `contracts/src/*.sol` |
| **Foundry (`forge`)** | Not installed in host Windows PATH | Command execution check |

---

## 3. Configuration & Secrets Handling

### Environment Variables & Settings (`backend/app/core/config.py` & `.env.example`)
Inspection confirms the project adheres to the PRD mandate: **No private keys, API secrets, or credentials committed to version control.**

| Setting Key | Default / Configured Value | Sensitive? | Purpose |
|---|---|---|---|
| `PROJECT_NAME` | `VERIDION Decentralized Legal Intelligence Protocol` | No | OpenAPI and metadata title |
| `VERSION` | `1.0.0` | No | Semantic protocol version |
| `API_V1_STR` | `/api/v1` | No | API prefix routing |
| `DEBUG` | `True` | No | Development debug flag |
| `DATABASE_URL` | `sqlite+aiosqlite:///./veridion.db` | No | Async SQLite (dev/test) / Postgres ready |
| `CHAIN_ID` | `11155111` (Sepolia Testnet) | No | EVM domain separator |
| `RPC_URL` | `http://127.0.0.1:8545` | No | EVM RPC endpoint |
| `EVALUATOR_ADDRESS` | `0x1234567890123456789012345678901234567890` | No | Authorized evaluator address |
| `ADMIN_ADDRESS` | `0x0987654321098765432109876543210987654321` | No | Protocol administrator address |
| `OPENAI_API_KEY` | `""` (Empty string) | Yes | Optional live provider key |
| `GEMINI_API_KEY` | `""` (Empty string) | Yes | Optional live provider key |
| `HF_API_TOKEN` | `""` (Empty string) | Yes | Optional fine-tuned HF model token |
| `HF_MODEL_ID` | `veridion-legal-finetuned` | No | Hugging Face model identifier |
| `HF_ENDPOINT_URL` | `""` (Empty string) | No | Optional local vLLM/Ollama endpoint |

---

## 4. Deployed Smart Contract Infrastructure (Sepolia Testnet)

As verified in `contracts/script/Deploy.s.sol`, `contracts/script/Lifecycle.s.sol`, `backend/contracts/deployments.json`, and `frontend/src/lib/deployments.json`:

```json
{
  "network": "sepolia",
  "chainId": 11155111,
  "CaseRegistry": "0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E",
  "AgentRegistry": "0x32d5D291e287fF173F803f5ee53Aef75BADb2006",
  "PredictionMarket": "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
  "EvidenceBounty": "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
  "ReputationSettlement": "0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c"
}
```

Receipt references are captured in `frontend/src/lib/lifecycle_sepolia.json` referencing confirmed Sepolia transaction hashes.

---

## 5. Automated Test Baseline Status

Running automated test commands on the pristine repository produces:

1. **Backend Tests** (`pytest backend/tests -v`):
   - **Total Tests**: 28
   - **Passed**: 28
   - **Failed**: 0
   - **Duration**: 3.95 seconds
2. **ML & Agent Swarm Tests** (`pytest ml -v`):
   - **Total Tests**: 66
   - **Passed**: 66
   - **Failed**: 0
   - **Duration**: 0.56 seconds
3. **Reproducible Benchmark Check** (`python scripts/run_local_tests.py`):
   - **Scenarios Evaluated**: 20 / 20
   - **Average Issue Recall**: 0.823
   - **Pre-push Gate Status**: `PASS` (Return code 0)

**Total automated test suite count**: **94 tests, 100% passing.**
