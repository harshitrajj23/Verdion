# VERIDION Protocol — Scientific Reproduction Commands

This document contains exact, reproducible CLI commands to verify all test suites, benchmark evaluations, agent performance metrics, and end-to-end lifecycles on Windows PowerShell.

---

## 1. Environment Activation & Dependencies

```powershell
# From workspace root
cd "C:\Users\DIVYANK BHARDWAJ\Desktop\Projects\veridion\Verdion"

# Verify Python version (Requires Python 3.11+)
.\.venv\Scripts\python --version

# Verify Node.js version (Requires Node 18+)
node --version
```

---

## 2. Automated Test Suites (94 CI Tests)

### Run Entire Test Suite (Backend + ML Swarm)
```powershell
# Executes all 94 automated tests (target: < 5 seconds)
.\.venv\Scripts\pytest -v
```

### Run Backend Integration Suite (28 Tests)
```powershell
# Executes API routers, case creation, market commit/reveal, bounty escrow, and report export
.\.venv\Scripts\pytest backend/tests -v
```

### Run ML Swarm & Autonomous Agent Suite (42 Tests)
```powershell
# Executes sentence splitter, validator, isolation fences, and agent swarm roles
.\.venv\Scripts\pytest ml/agents -v
```

### Run Deterministic Rule Engine Suite (5 Tests)
```powershell
# Executes GDPR Art 5(1)(b), 5(1)(e), 13, 22, and AI Act Art 50 statutory checks
.\.venv\Scripts\pytest ml/rules -v
```

---

## 3. Scientific Benchmark & Calibration Reproduction

### Run Discrimination & Separation Analysis (Train Split, N=14)
```powershell
# Computes positive vs negative separation and 95% bootstrap confidence intervals
.\.venv\Scripts\python ml/benchmark/discrimination_check.py
```

### Run Discrimination Unit Tests (3 Tests)
```powershell
# Validates bootstrap reproducibility with fixed seeds and separation assertions
.\.venv\Scripts\pytest ml/benchmark/test_discrimination.py -v
```

### Run Forecaster Calibration Check
```powershell
# Validates quadratic Brier scoring and population variance
.\.venv\Scripts\pytest ml/aggregation -v
```

---

## 4. Smart Contract Foundry Tests (EVM)

```powershell
cd contracts

# Build contracts using Solidity 0.8.24
forge build

# Execute comprehensive contract test suite (627 lines)
forge test -vvv
```

---

## 5. Live Server Execution

### Start FastAPI Backend Daemon
```powershell
.\.venv\Scripts\uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Start Next.js 14 Frontend Daemon
```powershell
cd frontend
npm run dev
```

### Seed Instant Demo Vertical Slice
```powershell
# Initializes clean demo case, 5 agents, argument graph, and Sepolia transaction record
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/demo/seed"
```
