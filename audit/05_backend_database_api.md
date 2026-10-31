# VERIDION Audit — Phases 12 & 13: Backend API & Database Persistence

**Audit Timestamp**: 2026-10-27T04:25:00+05:30  
**Lead Auditor**: Senior Full-Stack Engineer & Database Architect  
**Requirements Reference**: `VERIDION_Product_Requirements_Document_v1.0.pdf` (Sections 14 & 15)  
**Deliverable**: `audit/05_backend_database_api.md`  

---

## 1. Backend REST API Architecture

The backend is built with **FastAPI** (`0.110.0+`), running asynchronously with **Uvicorn** and validated by **Pydantic v2**.

### 1.1 Endpoint Route Coverage

All 16 routes specified in PRD Section 15.1 are implemented with explicit input/output validation schemas:

| Method | Route | Schema In / Out | Controller / Service | Status |
|---|---|---|---|---|
| `POST` | `/api/v1/cases` | `CaseCreateRequest` -> `CaseResponse` | `CaseService.create_case` | **VERIFIED PASS** |
| `GET` | `/api/v1/cases/{id}` | Path param -> `CaseResponse` | `CaseService.get_case` | **VERIFIED PASS** |
| `PATCH` | `/api/v1/cases/{id}` | `CaseUpdateRequest` -> `CaseResponse` | `CaseService.update_case` | **VERIFIED PASS** |
| `POST` | `/api/v1/cases/{id}/analyze` | Sync/async query -> `JobResponse` | `JobRunnerService.dispatch_analysis_job` | **VERIFIED PASS** |
| `GET` | `/api/v1/cases/{id}/analysis` | Path param -> `ArgumentGraphResponse` | `ArgumentService.get_argument_graph` | **VERIFIED PASS** |
| `GET` | `/api/v1/cases/{id}/agents` | Path param -> `CaseAgentsResponse` | `CaseService.get_case_agents` | **VERIFIED PASS** |
| `GET` | `/api/v1/cases/{id}/stream` | Path param -> Server-Sent Events | `CaseService.stream_full_analysis` | **VERIFIED PASS** |
| `GET` | `/api/v1/cases/{id}/report` | `format=json/markdown` -> `FinalCaseReport` | `ReportingService.generate_final_report` | **VERIFIED PASS** |
| `GET` | `/api/v1/cases/{id}/audit` | Path param -> `List[AuditEventResponse]` | `AuditService.get_case_audit_trail` | **VERIFIED PASS** |
| `POST` | `/api/v1/markets` | `MarketCreateRequest` -> `MarketResponse` | `MarketService.create_market` | **VERIFIED PASS** |
| `POST` | `/api/v1/markets/{id}/commit` | `MarketCommitRequest` -> `CommitResponse` | `MarketService.commit_forecast` | **VERIFIED PASS** |
| `POST` | `/api/v1/markets/{id}/reveal` | `MarketRevealRequest` -> `RevealResponse` | `MarketService.reveal_forecast` | **VERIFIED PASS** |
| `POST` | `/api/v1/markets/{id}/resolve` | `MarketResolveRequest` -> `MarketResponse` | `MarketService.propose_resolution` | **VERIFIED PASS** |
| `POST` | `/api/v1/markets/{id}/settle` | Caller param -> `SettlementResponse` | `MarketService.settle_market` | **VERIFIED PASS** |
| `POST` | `/api/v1/bounties` | `BountyCreateRequest` -> `BountyResponse` | `BountyService.create_bounty` | **VERIFIED PASS** |
| `POST` | `/api/v1/bounties/{id}/submissions` | `EvidenceSubmissionRequest` -> `SubmissionResponse` | `BountyService.submit_evidence` | **VERIFIED PASS** |
| `POST` | `/api/v1/submissions/{id}/challenge` | `SubmissionChallengeRequest` -> `SubmissionResponse` | `BountyService.challenge_submission` | **VERIFIED PASS** |
| `POST` | `/api/v1/bounties/{id}/settle` | `BountySettleRequest` -> `SettlementResponse` | `BountyService.settle_bounty` | **VERIFIED PASS** |
| `GET` | `/api/v1/agents/{id}/reputation` | Path param -> `ReputationResponse` | `AgentService.get_agent_reputation` | **VERIFIED PASS** |
| `POST` | `/api/v1/demo/seed` | None -> Full Seeder Response | `DemoService.seed_demo_workflow` | **VERIFIED PASS** |

---

## 2. Middleware & Reliability Verification

### 2.1 Idempotency Middleware (`IdempotencyMiddleware`)
- **Requirement**: PRD Section 13.4 & 15.1 ("Use idempotency keys for transaction-producing operations").
- **Implementation**: [`backend/app/core/middleware.py`](file:///C:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/core/middleware.py) intercepts `POST` and `PATCH` requests containing the `Idempotency-Key` header.
- **Verification**: `test_end_to_end.py::test_idempotency_middleware_replay` executes a request twice with the same idempotency key and asserts that the second response returns `X-Idempotent-Replay: true` with identical payload and status code.

### 2.2 Trace ID Middleware (`TraceIdMiddleware`)
- Intercepts or generates `X-Trace-ID` and binds it to `request.state.trace_id`.
- The trace ID is included in response headers and propagated to structured logs for end-to-end request tracing.

### 2.3 Standardized Error Responses
Exceptions inherit from `VeridionAPIException` with unique error codes matching PRD Section 15.4:
- `INVALID_SCOPE`: HTTP 400
- `SOURCE_UNAVAILABLE`: HTTP 404
- `AGENT_TIMEOUT`: HTTP 504
- `INVALID_FORECAST`: HTTP 422
- `COMMITMENT_MISMATCH`: HTTP 400
- `MARKET_CLOSED`: HTTP 409
- `UNAUTHORIZED_RESOLUTION`: HTTP 403
- `SETTLEMENT_ALREADY_DONE`: HTTP 409
- `CHAIN_RPC_ERROR`: HTTP 502

---

## 3. Database Schema & Persistence Audit

### 3.1 ORM Model Architecture
Defined in [`backend/app/models/entities.py`](file:///C:/Users/DIVYANK%20BHARDWAJ/Desktop/Projects/veridion/Verdion/backend/app/models/entities.py) with 11 primary relational tables:
1. `cases`: Primary case records with `scope_version`, facts JSON, status.
2. `source_documents`: Authoritative legal sources with effective dates, SHA-256 digests.
3. `evidence_passages`: Granular statutory passages referenced by claims.
4. `agents`: Registered agent records with roles, wallets, reputation, Brier scores.
5. `claims`: Verifiable propositions generated by agents with status (`SUPPORTED`/`UNSUPPORTED`).
6. `claim_evidence_links`: Foreign key linkages between claims and evidence passages.
7. `argument_edges`: Graph edges (`SUPPORTS`, `CONTRADICTS`, `QUALIFIES`, `DEPENDS_ON`, `SUPERSEDES`).
8. `prediction_markets`: Precise outcome definitions, deadlines, aggregate probabilities.
9. `forecasts`: Commit-reveal records, probabilities, nonces, commitment hashes.
10. `evidence_bounties` & `evidence_submissions`: Research tasks, anti-duplicate digests, review criteria.
11. `settlements` & `audit_events`: Tamper-evident transaction logs, UTC timestamps.

### 3.2 Migrations & Schema Versions
- Alembic configuration in `alembic.ini` and `backend/alembic/versions/2b2f920eafaf_initial_schema.py`.
- `init_db()` automatically provisions all tables upon startup if not existing.
- Supports both async SQLite for local fast testing and PostgreSQL for production deployments.
