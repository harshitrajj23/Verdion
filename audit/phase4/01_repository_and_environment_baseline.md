# VERIDION PHASE 4 — REPOSITORY AND ENVIRONMENT BASELINE REPORT

**Document ID:** `audit/phase4/01_repository_and_environment_baseline.md`  
**Execution Timestamp:** 2026-10-27T07:00:00+05:30  
**Phase Baseline Commit:** `a12d626b4778f9d12d78da61c1dae978944feda9`  
**Direct Ancestor Commit:** `ca33ac221ed5492fcd47c21874fb111f655734a3` (`origin/main` / `origin/Divyank`)  
**Active Branch:** `Divyank`  
**Target Architecture:** VERIDION Decentralized Legal Intelligence Protocol (EVM + Async Python FastAPI + Next.js 14)  

---

## 1. Executive Summary

Phase 4 begins from an established and verified baseline established in Phase 3. The working tree has been committed cleanly on branch `Divyank` (commit `a12d626`), building directly on top of the original verified baseline `ca33ac2`.

All 99 automated backend pytest tests and 11 Vitest frontend component tests are currently passing. This report documents the exact execution environment, dependency tree, configuration sources, and operational parameters prior to executing the Phase 4 external reality verifications and production readiness engineering.

---

## 2. Git Repository & Remote Status

| Property | Value | Observation / Verification |
| :--- | :--- | :--- |
| **Repository Root** | `C:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion` | Contains `.git` folder and root project structure |
| **Current Branch** | `Divyank` | Actively tracking remote branch |
| **Current Commit SHA** | `a12d626b4778f9d12d78da61c1dae978944feda9` | Full SHA recorded via `git rev-parse HEAD` |
| **Base Commit SHA** | `ca33ac221ed5492fcd47c21874fb111f655734a3` | Verified ancestor commit |
| **Remote URL** | `https://github.com/harshitrajj23/Verdion.git` | Configured as `origin` |
| **Working Tree Status** | Clean | Zero untracked or unstaged files at start of Phase 4 |
| **Git Safety Rule** | Enforced | No destructive git commands (`reset --hard`, `force push`) permitted |

---

## 3. Runtimes & Dependency Architecture

### 3.1 Python Runtime & Virtual Environment
- **Python Binary:** `.\.venv\Scripts\python.exe` (Version 3.11.9, 64-bit Windows)
- **FastAPI / Server:** FastAPI `0.115.11`, Uvicorn `0.34.0`, Starlette `0.46.0`
- **Data & ORM:** SQLAlchemy `2.0.38`, aiosqlite `0.21.0`, Pydantic `2.10.6`, pydantic-settings `2.8.0`
- **Cryptography & EVM:** `web3` `8.0.0`, `eth-utils` `5.3.0`, `eth-abi` `5.2.0`, `pycryptodome`
- **Testing & Quality:** Pytest `8.3.4`, pytest-asyncio `0.25.3`

### 3.2 Node.js & Frontend Environment
- **Node.js Version:** `v24.14.0` (LTS)
- **Package Manager:** `npm 11.9.0`
- **Framework:** Next.js `14.2.25` (App Router architecture)
- **UI & Styling:** React `18.3.1`, TailwindCSS `3.4.1`, Lucide-React `0.447.0`
- **Client Testing:** Vitest `4.1.12`, `@testing-library/react` `16.0.1`, `@testing-library/jest-dom` `6.5.0`

### 3.3 Smart Contract Infrastructure
- **Framework:** Foundry (`forge`, `cast`, `anvil`)
- **Solidity Version:** `^0.8.20`
- **Contracts Located:** `contracts/src/` (`CaseRegistry.sol`, `AgentRegistry.sol`, `PredictionMarket.sol`, `EvidenceBounty.sol`, `ReputationSettlement.sol`)
- **Compilation Artifacts:** `backend/contracts/` and `frontend/src/lib/deployments.json`

---

## 4. Database & Storage Baseline

- **Primary Database Engine:** SQLite via Async Engine (`sqlite+aiosqlite:///./veridion.db`)
- **Database File:** `C:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion\veridion.db` (Size: ~104 KB)
- **Schema Lifecycle:** SQLAlchemy declarative metadata with explicit `lazy="selectin"` relationship loaders to prevent async greenlet context errors.
- **Seeded Tables:**
  - `cases`: 4 cases stored (3 demonstration cases + 1 Phase 3 live verified E2E case)
  - `documents` & `evidence_passages`: Statutory legal texts (GDPR, EU AI Act, CJEU rulings) with SHA-256 digests
  - `agents`: 6 core protocol agents registered with wallets and credit balances
  - `prediction_markets`: 4 prediction markets with lifecycle states
  - `forecasts`: Cryptographic commitments and revealed probabilities
  - `evidence_bounties` & `bounty_submissions`: Active, challenged, and settled bounties
  - `audit_events`: Immutable audit trail with cryptographic hashes

---

## 5. Active Daemon Services

| Service | Protocol / Port | Process Command | Health / Status |
| :--- | :--- | :--- | :--- |
| **FastAPI Backend** | `http://127.0.0.1:8000` | `uvicorn backend.app.main:app --port 8000` | Operational (`/health` returns `{"status": "healthy"}`) |
| **Next.js Frontend** | `http://localhost:3000` | `npm run dev` | Operational (App Router, HTTP 200 on all routes) |
| **EVM RPC Target** | `https://ethereum-sepolia-rpc.publicnode.com` | Public Sepolia Node | Verified reachable (Chain ID: `11155111`) |

---

## 6. Baseline Verification Commands & Status

```bash
# 1. Backend Unit & Regression Suite
.\.venv\Scripts\pytest -q
# Result: 99 passed in 3.92s

# 2. Frontend Unit & Regression Suite
npm run test
# Result: 11 passed in 2.79s

# 3. Next.js Production Build
npm run build
# Result: 12/12 static/dynamic routes compiled cleanly (0 errors)
```

---

## 7. Baseline Conclusions & Next Steps

The repository is stable, reproducible, and internally consistent. The critical gaps identified for Phase 4 focus on:
1. Validating contract addresses on Ethereum Sepolia against public RPC nodes.
2. Eliminating phantom Etherscan links for simulated transactions and enforcing honest status labels.
3. Establishing modular regulatory ingestion adapters for EUR-Lex and CJEU with change detection and re-analysis queuing.
4. Implementing readiness/liveness health probes and production deployment configuration.
