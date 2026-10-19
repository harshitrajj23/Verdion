# 💻 VERIDION — Frontend Developer Integration Guide

Welcome! The VERIDION backend is fully built, tested, and exposes all REST & Server-Sent Events (SSE) endpoints needed to power the frontend interface.

---

## ⚡ Quick Start for Frontend Dev

### 1. Backend Server URL
- **Base API URL**: `http://localhost:8000/api/v1`
- **Interactive Swagger Docs**: [`http://localhost:8000/api/v1/docs`](http://localhost:8000/api/v1/docs)
- **CORS**: Pre-configured to accept requests from any origin (`http://localhost:3000` for Next.js, etc.).

### 2. TypeScript Types
We have already generated full TypeScript models for every entity and API response.  
👉 Simply copy [`docs/veridion-api-types.ts`](./veridion-api-types.ts) into your Next.js project as `src/types/veridion.ts`.

### 3. One-Click Demo Seeder (Instant Mock/Live Data)
Need sample data to design and test your UI immediately?
Send a `POST` request to:
```bash
POST http://localhost:8000/api/v1/demo/seed
```
This automatically initializes the legal corpus, 6 default agents, creates an AI customer analytics case, runs multi-agent investigation, commits/reveals prediction market forecasts, opens & settles an evidence bounty, and creates an audit trail!

---

## 🖥️ Screen-by-Screen Endpoint Cheat Sheet

### 1. Dashboard (PRD Section 16.1)
- **Get Active Cases**: `GET /api/v1/cases`
- **Get Open Prediction Markets**: `GET /api/v1/markets`
- **Get Active Evidence Bounties**: `GET /api/v1/bounties`
- **Get All Registered Agents**: `GET /api/v1/agents`
- **Get Global Audit Trail**: `GET /api/v1/audit?limit=20`

### 2. Case Workspace (PRD Section 16.2)
- **Create Case**: `POST /api/v1/cases`
  ```json
  {
    "title": "AI Customer Audio Training Assessment",
    "question": "Assess compliance risks of processing customer-support conversations to train an AI model",
    "jurisdiction": "EU",
    "assessment_date": "2026-10-19",
    "facts": {
      "data_categories": ["voice recordings", "account IDs"],
      "processing_purpose": "original: support resolution; secondary: LLM training",
      "user_notice_provided": false,
      "user_consent_obtained": false,
      "retention_policy": "indefinite",
      "deletion_mechanism": "manual refusal",
      "secondary_ai_training": true
    }
  }
  ```
- **Fetch Case Details**: `GET /api/v1/cases/{id}`
- **Update Case Facts / Increment Version**: `PATCH /api/v1/cases/{id}`

### 3. Agent Laboratory (PRD Section 16.3) — Real-Time Streaming
You can stream live multi-agent execution step-by-step using Server-Sent Events (SSE):
```typescript
const eventSource = new EventSource(`http://localhost:8000/api/v1/cases/${caseId}/stream`);

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log('Current Step:', data.status, data.message);
});

eventSource.addEventListener('agent_running', (e) => {
  const data = JSON.parse(e.data);
  // Highlight active agent (LEGAL_RESEARCHER, LEGAL_INTERPRETER, ADVERSARIAL_RESEARCHER, etc.)
});

eventSource.addEventListener('agent_complete', (e) => {
  const data = JSON.parse(e.data);
  // Render completed claims, findings, or counterarguments
});

eventSource.addEventListener('analysis_complete', (e) => {
  const data = JSON.parse(e.data);
  // Analysis finished! Contains full argument_graph and ranked uncertainties
  eventSource.close();
});
```

### 4. Interactive Argument Graph Explorer (PRD Section 16.4)
- **Fetch Argument Graph**: `GET /api/v1/cases/{id}/analysis`
  - Returns:
    - `claims`: Array of structured claims with type, confidence, and status (`SUPPORTED`, `UNSUPPORTED`, `CONTESTED`).
    - `evidence_links`: Connects claims to statutory passages (`SUPPORTS`, `REFUTES`).
    - `edges`: Relations between claims (`SUPPORTS`, `CONTRADICTS`, `QUALIFIES`, `DEPENDS_ON`).
    - `conflicts`: Filtered list of contradiction edges between adversarial objections and risk findings!

### 5. Prediction Market Page (PRD Section 16.5)
- **List Markets for Case**: `GET /api/v1/markets?case_id={case_id}`
- **Get Single Market**: `GET /api/v1/markets/{market_id}` (contains `aggregate_probability`, `disagreement_variance`, `sample_size`, `status`)
- **Commit Forecast**: `POST /api/v1/markets/{market_id}/commit`
  ```json
  {
    "agent_id": "agent_legal_researcher",
    "commitment_hash": "0x..."
  }
  ```
- **Reveal Forecast**: `POST /api/v1/markets/{market_id}/reveal`
  ```json
  {
    "agent_id": "agent_legal_researcher",
    "probability": 0.85,
    "evidence_digest": "0x...",
    "nonce": "0x..."
  }
  ```
- **Propose Resolution (Evaluator)**: `POST /api/v1/markets/{market_id}/resolve`
- **Settle Market**: `POST /api/v1/markets/{market_id}/settle` (computes Brier score and awards credits)

### 6. Evidence Bounty Portal (PRD Section 16.6)
- **Create Bounty**: `POST /api/v1/bounties`
- **Submit Evidence**: `POST /api/v1/bounties/{bounty_id}/submissions`
  ```json
  {
    "contributor_address": "0xUserWalletAddress",
    "title": "EDPB Guidelines 3/2019 Citation",
    "source_reference": "EDPB Guidelines 3/2019 paragraph 44",
    "content": "Secondary processing of customer interactions for AI algorithmic training requires a separate compatibility test under Art 6(4).",
    "provenance": { "source": "Official EU Gazette" }
  }
  ```
- **Challenge Submission**: `POST /api/v1/submissions/{submission_id}/challenge`
- **Settle Bounty**: `POST /api/v1/bounties/{bounty_id}/settle`

### 7. Audit Explorer & Final 10-Section Report (PRD Section 16.7 & 16.8)
- **Get Case Audit Trail**: `GET /api/v1/cases/{case_id}/audit`
  - Returns ordered list of blockchain transaction hashes, actor addresses, and SHA-256 digests.
- **Get 10-Section Final Compliance Report**: `GET /api/v1/cases/{case_id}/report`
  - Contains all 10 PRD sections ready to render or export to PDF:
    1. Executive Summary & Scope
    2. Facts and Assumptions
    3. Relevant Sources and Effective Dates
    4. Principal Claims & Evidence
    5. Counterarguments & Conflicts
    6. Risk Findings & Limitations
    7. Prediction Market Forecasts & Calibration
    8. Unresolved Uncertainties & Bounties
    9. Recommended Next Steps & Legal Disclaimer
    10. Audit Trail & Transaction Hashes
