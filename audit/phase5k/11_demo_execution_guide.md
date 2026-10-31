# VERIDION Phase 5K — Deliverable 11: Demo Execution Guide

## Quickstart for Judges and Evaluators

### 1. Start Backend Server
```powershell
cd Verdion
$env:PYTHONPATH = "Verdion"
Verdion\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000
```

### 2. Start Frontend Server
```powershell
cd Verdion\frontend
npm run dev
```

### 3. Key Demonstration Workflows

1. **Case Submission & 6-Agent Dialectic:** Navigate to `http://localhost:3000/cases`. Create a case assessing workplace biometric emotion recognition under GDPR Art 9 & EU AI Act Art 5.
2. **Argument Graph Inspection:** View the competing claims, contrary evidence edges, and deontic citations.
3. **Commit-Reveal Prediction Market:** Open `http://localhost:3000/markets` to inspect on-chain 6-field forecast commitments.
4. **Independent Merkle Audit Trail:** Open `http://localhost:3000/audit` to independently recompute and verify the cryptographic Merkle root.
