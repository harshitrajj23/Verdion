# VERIDION — Frontend Engineering Handoff Document

## 1. Product & Architecture Overview

VERIDION is an **Auditable Regulatory Decision Infrastructure** under **Option C**.
It is not a generic legal chatbot. Every regulatory conclusion is grounded in verifiable legal sources, evaluated by a 6-agent dialectic committee, probabilistically forecasted on-chain with a 6-field commit-reveal protocol, and sealed into a tamper-evident cryptographic Merkle decision record.

### Core Architectural Layers:
1. **API Layer:** FastAPI with standard JSON schemas, trace IDs, and idempotency keys.
2. **Regulatory Retrieval Layer:** Inverted index and subword N-gram matching across EUR-Lex, CJEU, and EDPB statutory corpora.
3. **6-Agent System:**
   - `LEGAL_RESEARCHER`: Statutory extraction & passage identification (`RULE_DERIVED`).
   - `LEGAL_INTERPRETER`: Fact-to-law condition evaluation (`RULE_DERIVED`).
   - `ADVERSARIAL_RESEARCHER`: Statutory defenses & counterarguments (`MODEL_ESTIMATED` / `OFFLINE_FALLBACK`).
   - `EVIDENCE_VERIFIER`: 9-dimensional grounding & digest verification (`CRYPTOGRAPHIC_INTEGRITY`).
   - `QUANTITATIVE_FORECASTER`: Calibrated probability forecasting (`EMPIRICALLY_CALIBRATED`).
   - `COORDINATOR_SYNTHESIS`: Dialectic argument graph synthesis & Merkle sealing (`RULE_DERIVED`).
4. **Audit & Decision Layer:** Canonical JSON serialization, Merkle tree sealing, independent offline verifier.
5. **Prediction Market Layer:** 6-field keccak256 commit-reveal protocol matching Solidity `PredictionMarket.sol`.

---

## 2. Server Startup & Connection Details

### Start the Backend Server:
```powershell
cd Verdion
$env:PYTHONPATH = "Verdion"
Verdion\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start the Frontend Server:
```powershell
cd Verdion\frontend
npm run dev
```

### Frontend Proxy Configuration:
The Next.js 14 frontend automatically proxies `/api/v1/:path*` to `http://127.0.0.1:8000/api/v1/:path*` via `next.config.mjs`. In custom frontend environments, configure `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1`.

---

## 3. Standard Request & Response Envelopes

### Successful Response:
```json
{
  "id": "case_12345",
  "status": "COMPLETED",
  "scope_version": 1,
  "created_at": "2026-10-31T22:30:00Z"
}
```

### Error Response:
```json
{
  "detail": "Case 'case_unknown' not found"
}
```
HTTP status codes are standard: `200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`.

---

## 4. Key Status Enums & Data Types

- **Case Status:** `DRAFT`, `ANALYZING`, `COMPLETED`, `FAILED`
- **Workflow State:** `INTAKE`, `RETRIEVAL`, `ANALYSIS`, `SYNTHESIS`, `DECISION_SEALED`, `AUDIT_EXPORTED`
- **Confidence Type:** `RULE_DERIVED`, `MODEL_ESTIMATED`, `CRYPTOGRAPHIC_INTEGRITY`, `EMPIRICALLY_CALIBRATED`, `UNCALIBRATED`
- **Grounding Dimensions (9):** `PASSAGE_INTEGRITY`, `SOURCE_AUTHENTICITY`, `CITATION_VALIDITY`, `QUOTATION_ACCURACY`, `SEMANTIC_SUPPORT`, `LEGAL_ENTAILMENT`, `FACT_TO_LAW_APPLICABILITY`, `JURISDICTIONAL_VALIDITY`, `TEMPORAL_VALIDITY`
- **Grounding Status:** `VERIFIED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `UNVERIFIED`, `HUMAN_REVIEW_REQUIRED`
- **Commitment Status:** `COMMITTED`, `REVEALED`, `MISMATCH`, `EXPIRED`
