# VERIDION — Known Issues & Frontend Integration Notes

## 1. Resolved During Phase 5K / Final Execution
- **`DEF-5K-01`**: `EvidenceGroundingService` omitted `UNVERIFIED` from fail-closed failure check. (Resolved).
- **`DEF-5K-02`**: Next.js Google Fonts online download blocked in offline build. (Resolved with local CSS font variables).
- **`DEF-5K-03`**: AsyncIO `ProactorEventLoop` socketpair hang in Windows sandbox. (Resolved with synchronous execution pathways).
- **`DEF-5K-04`**: Commitment digest non-hex input parsing. (Resolved with explicit ValueError rejection).

## 2. Frontend Engineer Notes
- **API URL:** Default API base URL is `/api/v1` (proxied by Next.js to `http://127.0.0.1:8000/api/v1`).
- **Synchronous Analysis Flag:** When calling `POST /api/v1/cases/{case_id}/analyze`, pass `?sync=true` if you want the full analysis returned in the HTTP response, or `?sync=false` to receive a `jobId` for background polling/streaming.
- **SSE Streaming:** `GET /api/v1/cases/{case_id}/stream` provides real-time Server-Sent Events (SSE) for the interactive Agent Laboratory.
