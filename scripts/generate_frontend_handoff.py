"""
Generates the complete Frontend Engineering Handoff Package for VERIDION Option C:
- frontend-handoff/openapi.json
- frontend-handoff/FRONTEND_HANDOFF.md
- frontend-handoff/API_CONTRACT.md
- frontend-handoff/FRONTEND_DATA_MODELS.md
- frontend-handoff/FRONTEND_INTEGRATION_CHECKLIST.md
- frontend-handoff/.env.example
- frontend-handoff/examples/*.json
Mirrored to both root/ and Verdion/ directories.
"""

import json
import os
import sys
from pathlib import Path

# Add Verdion to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VERDION_DIR = ROOT_DIR / "Verdion"
sys.path.insert(0, str(VERDION_DIR))

from backend.app.main import app

HANDOFF_DIR = ROOT_DIR / "frontend-handoff"
MIRROR_HANDOFF_DIR = VERDION_DIR / "frontend-handoff"
EXAMPLES_DIR = HANDOFF_DIR / "examples"
MIRROR_EXAMPLES_DIR = MIRROR_HANDOFF_DIR / "examples"

HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
MIRROR_HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
MIRROR_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def write_and_mirror(relative_path: str, content: str):
    p1 = HANDOFF_DIR / relative_path
    p2 = MIRROR_HANDOFF_DIR / relative_path
    p1.parent.mkdir(parents=True, exist_ok=True)
    p2.parent.mkdir(parents=True, exist_ok=True)
    with open(p1, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    with open(p2, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"  [HANDOFF ARTIFACT] {relative_path}")


def write_json_and_mirror(relative_path: str, data: dict):
    content = json.dumps(data, indent=2, default=str)
    write_and_mirror(relative_path, content)


def main():
    print("=================================================================")
    print("GENERATING FRONTEND ENGINEERING HANDOFF PACKAGE")
    print("=================================================================")

    # 1. Export Live OpenAPI Schema
    openapi_schema = app.openapi()
    write_json_and_mirror("openapi.json", openapi_schema)
    print(f"Exported live OpenAPI schema with {len(openapi_schema.get('paths', {}))} endpoints.")

    # 2. Generate Example JSON Payloads
    examples = {
        "create_case.json": {
            "title": "Autonomous AI Recruitment Screening & Biometric Emotion Analysis",
            "jurisdiction": "EU",
            "statutes": ["GDPR", "EU_AI_ACT"],
            "facts": {
                "system_type": "Recruitment AI",
                "biometric_processing": True,
                "data_categories": ["biometric", "facial_video"],
                "user_consent_obtained": False,
                "user_notice_provided": False,
                "human_in_the_loop": False,
                "solely_automated_decision": True,
                "retention_policy": "indefinite"
            },
            "assessment_date": "2026-10-31"
        },
        "analyze_case.json": {
            "sync": True
        },
        "case_response.json": {
            "id": "case_alpha_recruitment_01",
            "title": "Autonomous AI Recruitment Screening & Biometric Emotion Analysis",
            "jurisdiction": "EU",
            "status": "COMPLETED",
            "scope_version": 1,
            "facts": {
                "system_type": "Recruitment AI",
                "biometric_processing": True,
                "solely_automated_decision": True
            },
            "created_at": "2026-10-31T22:30:00Z",
            "updated_at": "2026-10-31T22:30:05Z"
        },
        "agent_execution_response.json": {
            "case_id": "case_alpha_recruitment_01",
            "agents": [
                {
                    "agentId": "agent_legal_researcher",
                    "role": "LEGAL_RESEARCHER",
                    "status": "ACTIVE",
                    "confidence_contract": {
                        "raw_confidence": 0.95,
                        "calibrated_confidence": 0.95,
                        "confidence_type": "RULE_DERIVED",
                        "calibration_status": "HEURISTIC_BOUNDED",
                        "uncertainty_score": 0.05,
                        "inference_mode": "DETERMINISTIC_RULES",
                        "model_identifier": "deterministic_rule_engine_v1.2"
                    },
                    "claimsCount": 2
                },
                {
                    "agentId": "agent_adversarial_researcher",
                    "role": "ADVERSARIAL_RESEARCHER",
                    "status": "ACTIVE",
                    "confidence_contract": {
                        "raw_confidence": 0.70,
                        "calibrated_confidence": 0.65,
                        "confidence_type": "MODEL_ESTIMATED",
                        "calibration_status": "UNCALIBRATED",
                        "uncertainty_score": 0.45,
                        "inference_mode": "OFFLINE_FALLBACK",
                        "model_identifier": "mistralai/Mistral-7B-Instruct-v0.2"
                    },
                    "claimsCount": 1
                }
            ]
        },
        "evidence_response.json": {
            "id": "EV-EU-AIACT-ART5",
            "evidence_id": "EV-EU-AIACT-ART5",
            "passage_reference": "EU AI Act Art. 5(1)(f)",
            "digest": "0x4f128ab8d7c1829e0182374619b0283c74819283748291029384758392019283",
            "text": "The placing on the market, the putting into service or the use of AI systems to infer emotions of a natural person in the areas of workplace and education shall be prohibited.",
            "jurisdiction": "EU",
            "authority": "Regulation (EU) 2024/1689",
            "provenance": "EUR_LEX",
            "effective_date": "2024-08-02",
            "url": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
        },
        "decision_record_response.json": {
            "decision_id": "dec_case_alpha_recruitment_01_v1",
            "case_id": "case_alpha_recruitment_01",
            "case_version": 1,
            "record_digest": "0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456",
            "orchestration_version": "VERIDION_ORCHESTRATION_V1",
            "software_version": "veridion-core@1.0.0",
            "verification_status": "VERIFIED_INTEGRITY",
            "claims_verified": 4,
            "passages_verified": 2,
            "created_at": "2026-10-31T22:30:10Z"
        },
        "forecast_response.json": {
            "forecast_id": "fc_market_biometric_01",
            "market_id": "mkt_biometric_recruitment_01",
            "agent_id": "agent_quantitative_forecaster",
            "commitment_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "probability": 0.85,
            "reveal_status": "REVEALED",
            "brier_score": 0.0225,
            "commit_tx_hash": "0xcommit_simulated_tx_hash_01",
            "reveal_tx_hash": "0xreveal_simulated_tx_hash_01"
        },
        "verification_response.json": {
            "decision_id": "dec_case_alpha_recruitment_01_v1",
            "case_id": "case_alpha_recruitment_01",
            "is_valid": True,
            "stored_digest": "0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456",
            "recomputed_digest": "0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456",
            "verification_status": "VERIFIED_INTEGRITY",
            "claims_verified": 4,
            "sources_verified": 2,
            "passages_verified": 2,
            "audit_events_count": 8
        }
    }

    for name, data in examples.items():
        write_json_and_mirror(f"examples/{name}", data)

    # 3. Generate .env.example
    env_example_content = """# VERIDION Backend Environment Configuration Example
# Copy this file to Verdion/.env or set environment variables in your runtime.

# Application Configuration
PROJECT_NAME="VERIDION Legal Intelligence Protocol"
VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=False
API_V1_STR="/api/v1"

# CORS Configuration (comma-separated origins)
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Database Configuration (Defaults to SQLite veridion.db)
DATABASE_URL="sqlite+aiosqlite:///veridion.db"

# Blockchain & Prediction Market Configuration
CHAIN_ID=31337
EVALUATOR_ADDRESS="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
PREDICTION_MARKET_ADDRESS="0x5FbDB2315678afecb367f032d93F642f64180aa3"

# Model Provider Configuration (Optional - Defaults to safe local deterministic fallback)
HUGGINGFACE_API_KEY=""
OLLAMA_BASE_URL="http://127.0.0.1:11434"
OPENAI_COMPATIBLE_API_KEY=""
OPENAI_COMPATIBLE_BASE_URL=""
DEFAULT_MODEL_ID="mistralai/Mistral-7B-Instruct-v0.2"
"""
    write_and_mirror(".env.example", env_example_content)

    # 4. Generate FRONTEND_HANDOFF.md
    frontend_handoff_md = """# VERIDION — Frontend Engineering Handoff Document

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
Verdion\\.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start the Frontend Server:
```powershell
cd Verdion\\frontend
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
"""
    write_and_mirror("FRONTEND_HANDOFF.md", frontend_handoff_md)

    # 5. Generate API_CONTRACT.md
    api_contract_md = """# VERIDION — Backend API Contract Reference

This document describes all authoritative backend endpoints available to the frontend.

## 1. System & Capabilities
- **`GET /api/v1/health`**: Service availability & DB connectivity.
- **`GET /api/v1/system/status`**: Subsystem operational status report.
- **`GET /api/v1/system/capabilities`**: Supported jurisdictions, statutes, and agent roles.

## 2. Regulatory Cases
- **`POST /api/v1/cases`**: Creates a new case with facts and jurisdiction.
- **`GET /api/v1/cases`**: Lists registered cases (supports `?provenance=OPERATIONAL|DEMO` and `?exclude_test=true`).
- **`GET /api/v1/cases/{case_id}`**: Retrieves case metadata and lifecycle status.
- **`PATCH /api/v1/cases/{case_id}`**: Updates case facts or scope, bumping `scope_version`.
- **`POST /api/v1/cases/{case_id}/analyze`**: Triggers 6-agent analysis (`?sync=true` for synchronous execution).
- **`GET /api/v1/cases/{case_id}/execution`**: Full multi-agent execution status, timing, and errors.
- **`GET /api/v1/cases/{case_id}/agents`**: Agent outputs and claims for this case.
- **`GET /api/v1/cases/{case_id}/analysis`**: Argument graph, claims, and dialectic tension edges.
- **`GET /api/v1/cases/{case_id}/report`**: Comprehensive 10-section final regulatory report (supports `?format=json|markdown`).
- **`GET /api/v1/cases/{case_id}/workspace`**: Unified single-call decision workspace object.

## 3. Legal Sources & Passages
- **`GET /api/v1/sources`**: Lists legal sources with provenance and passage counts.
- **`GET /api/v1/sources/{source_id}`**: Retrieves single source document by ID.
- **`GET /api/v1/sources/{source_id}/passages`**: Lists passages extracted from a source document.
- **`POST /api/v1/sources/search`**: Searches statutory passages via term & cosine matching.
- **`POST /api/v1/sources/refresh`**: Reinitializes authoritative statutory corpora.

## 4. Evidence & 9-Dimensional Grounding
- **`GET /api/v1/evidence`**: Lists verified evidence passages with SHA-256 digests.
- **`GET /api/v1/evidence/{evidence_id}`**: Retrieves single passage by ID.
- **`POST /api/v1/evidence/verify`**: Evaluates claim grounding across all 9 discrete dimensions.
- **`GET /api/v1/cases/{case_id}/evidence`**: Retrieves all evidence passages bound to a case.

## 5. Multi-Agent Platform
- **`GET /api/v1/agents`**: Lists the 6 specialized agents and calibration scores.
- **`GET /api/v1/agents/{agent_id}`**: Retrieves single agent status and wallet.
- **`GET /api/v1/agents/{agent_id}/reputation`**: Empirical Brier score and reputation record.
- **`GET /api/v1/agents/{agent_id}/reputation/history`**: Chronological reputation change log.
- **`GET /api/v1/agents/executions/{execution_id}`**: Execution trace and timing metadata.

## 6. Canonical Decision Records
- **`GET /api/v1/decisions`**: Lists canonical sealed decision records.
- **`POST /api/v1/decisions`**: Builds and seals a Decision Record for a case.
- **`GET /api/v1/decisions/{decision_id}`**: Retrieves canonical decision record by ID or case_id.
- **`GET /api/v1/decisions/{decision_id}/verify`**: Independently verifies cryptographic SHA-256 digest.
- **`GET /api/v1/decisions/{decision_id}/provenance`**: Complete evidence provenance lineage.

## 7. Forecasting & Commitments
- **`GET /api/v1/forecasts`**: Lists agent forecasts.
- **`POST /api/v1/forecasts`**: Submits forecast with 6-field commitment hash.
- **`GET /api/v1/forecasts/{forecast_id}`**: Reads forecast record by ID.
- **`GET /api/v1/forecasts/{forecast_id}/metrics`**: Proper scoring Brier evaluation metrics.
- **`GET /api/v1/commitments`**: Lists prediction market commitments.
- **`POST /api/v1/commitments`**: Submits raw commitment hash.
- **`GET /api/v1/commitments/{commitment_id}`**: Reads commitment record.
- **`POST /api/v1/commitments/{commitment_id}/reveal`**: Reveals probability, digest, and nonce.
- **`GET /api/v1/commitments/{commitment_id}/verify`**: Independently verifies commitment against revealed fields.

## 8. Cryptographic Audit Trail
- **`GET /api/v1/audit`** & **`GET /api/v1/audit/events`**: Chronological audit events with hash links.
- **`GET /api/v1/audit/chain/{case_id}`** & **`GET /api/v1/audit/verify`**: Verifies cryptographic hash chain.
- **`GET /api/v1/audit/records/{record_id}`**: Retrieves single audit event record.
- **`GET /api/v1/audit/package/{case_id}`**: Exports standalone self-contained offline audit package.
- **`POST /api/v1/audit/verify-package`**: Validates uploaded audit package offline.
"""
    write_and_mirror("API_CONTRACT.md", api_contract_md)

    # 6. Generate FRONTEND_DATA_MODELS.md
    frontend_models_md = """# VERIDION — Frontend TypeScript Data Models

The following TypeScript definitions match the backend Pydantic schemas:

```typescript
export interface Case {
  id: string;
  title: string;
  jurisdiction: "EU" | "US-CA" | "GLOBAL";
  status: "DRAFT" | "ANALYZING" | "COMPLETED" | "FAILED";
  scope_version: number;
  facts: Record<string, any>;
  assessment_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ConfidenceContract {
  raw_confidence: number;
  calibrated_confidence?: number;
  confidence_type: "RULE_DERIVED" | "MODEL_ESTIMATED" | "CRYPTOGRAPHIC_INTEGRITY" | "EMPIRICALLY_CALIBRATED" | "UNCALIBRATED";
  calibration_status: "UNCALIBRATED" | "HEURISTIC_BOUNDED" | "EMPIRICALLY_CALIBRATED";
  uncertainty_score: number;
  supporting_evidence_count: number;
  contradicting_evidence_count: number;
  inference_mode: string;
  model_identifier: string;
}

export interface EvidenceRef {
  evidence_id: string;
  passage_reference: string;
  digest: string;
  relationship?: "SUPPORTS" | "REFUTES" | "QUALIFIES";
  relevance_score?: number;
}

export interface Claim {
  id: string;
  claim_text: string;
  claim_type: "STATUTORY_INTERPRETATION" | "FACTUAL_MAPPING" | "RISK_ASSESSMENT" | "EXCEPTION";
  confidence: number;
  confidence_rationale: string;
  is_supported: boolean;
  evidence_refs: EvidenceRef[];
  confidence_contract?: ConfidenceContract;
}

export interface EvidencePassage {
  id: string;
  evidence_id: string;
  passage_reference: string;
  digest: string;
  text: string;
  jurisdiction: string;
  authority: string;
  provenance: string;
  effective_date?: string;
  url?: string;
}

export interface ClaimGroundingResult {
  overall_status: "VERIFIED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED" | "UNVERIFIED" | "HUMAN_REVIEW_REQUIRED";
  dimension_statuses: Record<string, string>;
  dimension_scores: Record<string, number>;
  dimension_rationales: Record<string, string>;
  is_fully_grounded: boolean;
  requires_human_review: boolean;
  audit_notes: string[];
}

export interface CanonicalDecisionRecord {
  decision_id: string;
  case_id: string;
  case_version: number;
  record_digest: string;
  orchestration_version: string;
  software_version: string;
  analysis_timestamp: string;
  evidence_sources: any[];
  evidence_passages: EvidencePassage[];
  claims: Claim[];
  audit_events: any[];
}

export interface ForecastCommitment {
  id: string;
  market_id: string;
  agent_id: string;
  commitment_hash: string;
  probability?: number;
  evidence_digest?: string;
  nonce?: string;
  reveal_status: "COMMITTED" | "REVEALED" | "MISMATCH" | "EXPIRED";
  brier_score?: number;
  created_at: string;
  revealed_at?: string;
}

export interface AuditEvent {
  id: string;
  sequence_number: number;
  case_id: string;
  event_type: string;
  actor: string;
  payload: Record<string, any>;
  event_digest: string;
  previous_digest: string;
  timestamp: string;
}
```
"""
    write_and_mirror("FRONTEND_DATA_MODELS.md", frontend_models_md)

    # 7. Generate FRONTEND_INTEGRATION_CHECKLIST.md
    checklist_md = """# VERIDION — Frontend Integration Checklist

This checklist guides the frontend engineer through connecting the UI to the backend:

- [ ] **1. Backend Health Check:** Probe `GET /api/v1/health` -> verify status is `healthy`.
- [ ] **2. System Capabilities:** Probe `GET /api/v1/system/capabilities` -> verify 6 agents and 9 grounding dimensions.
- [ ] **3. Case Creation Flow:**
  - [ ] Submit `POST /api/v1/cases` with title, jurisdiction, and facts.
  - [ ] Receive `case_id` and initial status `DRAFT`.
- [ ] **4. Multi-Agent Analysis Execution:**
  - [ ] Trigger `POST /api/v1/cases/{case_id}/analyze?sync=true`.
  - [ ] Observe transition to `COMPLETED`.
  - [ ] Fetch agent outputs via `GET /api/v1/cases/{case_id}/agents`.
- [ ] **5. Argument Graph & Dialectic Viewer:**
  - [ ] Fetch graph via `GET /api/v1/cases/{case_id}/analysis`.
  - [ ] Render claims (nodes) and support/contradict relationships (edges).
- [ ] **6. Evidence & Grounding Exploration:**
  - [ ] Fetch bound evidence via `GET /api/v1/cases/{case_id}/evidence`.
  - [ ] Verify 9-dimensional status display (`GET /api/v1/evidence/verify`).
- [ ] **7. Prediction Market & Commit-Reveal:**
  - [ ] Fetch markets via `GET /api/v1/markets?case_id={case_id}`.
  - [ ] Submit forecast commitment via `POST /api/v1/commitments`.
  - [ ] Reveal commitment via `POST /api/v1/commitments/{id}/reveal`.
  - [ ] Verify commit-reveal parity via `GET /api/v1/commitments/{id}/verify`.
- [ ] **8. Canonical Decision Record Viewer:**
  - [ ] Fetch decision via `GET /api/v1/decisions/{case_id}`.
  - [ ] Display verified SHA-256 record digest.
  - [ ] Verify decision integrity via `GET /api/v1/decisions/{case_id}/verify`.
- [ ] **9. Independent Audit Verification:**
  - [ ] Fetch cryptographic audit chain via `GET /api/v1/audit/chain/{case_id}`.
  - [ ] Export self-contained audit package via `GET /api/v1/audit/package/{case_id}`.
  - [ ] Verify package via `POST /api/v1/audit/verify-package`.
"""
    write_and_mirror("FRONTEND_INTEGRATION_CHECKLIST.md", checklist_md)

    print("\nAll Frontend Handoff documents, examples, and OpenAPI schemas generated and mirrored successfully!")


if __name__ == "__main__":
    main()

