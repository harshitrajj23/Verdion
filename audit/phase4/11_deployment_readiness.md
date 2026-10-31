# VERIDION PHASE 4 — DEPLOYMENT READINESS REPORT

**Document ID:** `audit/phase4/11_deployment_readiness.md`  
**Execution Timestamp:** 2026-10-27T07:44:00+05:30  
**Target Environment:** Local / Staging / Production Containerized Host  
**Operating Systems Supported:** Windows 10/11 64-bit, Linux Ubuntu 22.04 LTS, macOS (Apple Silicon / Intel)  

---

## 1. Executive Summary

This report evaluates whether VERIDION can run reliably from a clean, documented environment. It defines the exact environment prerequisites, configuration mechanisms, health probe endpoints, startup commands, and operational procedures for production and evaluation deployments.

---

## 2. System Architecture & Prerequisites

### 2.1 Backend Prerequisites
- **Python:** 3.11+ (verified on Python 3.11.9)
- **Virtual Environment:** Recommended (`python -m venv .venv`)
- **Dependencies:** Installed via `pip install -r backend/requirements.txt`
  - Core: FastAPI 0.115+, Uvicorn 0.34+, Pydantic 2.10+, SQLAlchemy 2.0+, aiosqlite 0.21+
  - Web3 & Crypto: web3 8.0+, pycryptodome, eth-utils

### 2.2 Frontend Prerequisites
- **Node.js:** v20.x or v24.x LTS (verified on v24.14.0)
- **Package Manager:** npm (verified on npm 11.9.0)
- **Framework:** Next.js 14.2.25+ (App Router)
- **Build Output:** Standalone static/dynamic server assets (`.next/standalone`)

### 2.3 Network Access
- Outbound HTTPS to `https://ethereum-sepolia-rpc.publicnode.com` (Chain ID 11155111) for on-chain contract and receipt queries.
- Outbound HTTPS to EUR-Lex and CJEU Curia endpoints for regulatory feed updates.

---

## 3. Environment Configuration (`.env`)

The application loads configuration via Pydantic `BaseSettings` (`backend/app/core/config.py`). Recommended production `.env` template:

```env
# ── Server & Protocol ──
PROJECT_NAME="VERIDION Legal Intelligence Protocol"
VERSION="1.0.0"
ENVIRONMENT="production"
PORT=8000
HOST="0.0.0.0"

# ── Database ──
DATABASE_URL="sqlite+aiosqlite:///./veridion.db"

# ── Blockchain & Web3 ──
CHAIN_ID=11155111
SEPOLIA_RPC_URL="https://ethereum-sepolia-rpc.publicnode.com"

# Verified Smart Contract Deployments (Sepolia)
CASE_REGISTRY_ADDRESS="0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E"
AGENT_REGISTRY_ADDRESS="0x32d5D291e287fF173F803f5ee53Aef75BADb2006"
PREDICTION_MARKET_ADDRESS="0xFF5e85547E443e3d50b393E09885c6Eb9671EE27"
EVIDENCE_BOUNTY_ADDRESS="0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46"
REPUTATION_SETTLEMENT_ADDRESS="0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c"

# Protocol Admin & Evaluator Addresses
EVALUATOR_ADDRESS="0x1234567890123456789012345678901234567890"
ADMIN_ADDRESS="0x0987654321098765432109876543210987654321"

# ── AI Model Providers (Optional; Deterministic Rules run if omitted) ──
HF_API_TOKEN=""
HF_MODEL_ID="Qwen/Qwen2.5-Coder-32B-Instruct"
OLLAMA_ENDPOINT="http://localhost:11434/v1"
```

---

## 4. Health Probes & Observability

### 4.1 Liveness Probe
- **Endpoint:** `GET /health`
- **Response:** HTTP 200 OK
```json
{
  "status": "healthy",
  "service": "veridion-backend",
  "version": "1.0.0",
  "chain_id": 11155111,
  "database": "connected"
}
```

### 4.2 Readiness Probe
- **Endpoint:** `GET /api/v1/integrations/status`
- **Validates:**
  1. SQLite database readiness (`SELECT 1`).
  2. Ethereum Sepolia RPC connectivity and expected Chain ID (`11155111`).
  3. AI model provider configuration state.
  4. Verified smart contract address bindings.

---

## 5. Deployment Commands & Runbook

```bash
# 1. Setup Backend Environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt

# 2. Run Backend Verification Tests
.\.venv\Scripts\pytest -q
# Target: 105 passed

# 3. Launch Backend Daemon
.\.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 4. Setup Frontend Environment
cd frontend
npm install

# 5. Run Frontend Verification Tests
npm test
# Target: 11 passed

# 6. Build Next.js Production Assets
npm run build
# Target: 12/12 routes compiled cleanly

# 7. Launch Frontend Production Server
npm start -- -p 3000
```

---

## 6. Verification Verdict

**Status: PASS**. The application initializes cleanly, passes all regression and unit tests, complies with standard health probe specifications, and provides deterministic fallback paths when external AI or testnet keys are omitted.
