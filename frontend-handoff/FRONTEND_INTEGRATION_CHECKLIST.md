# VERIDION — Frontend Integration Checklist

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
