# VERIDION — Backend API Contract Reference

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
