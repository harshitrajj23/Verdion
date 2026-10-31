# Audit 09: API Reality and Route-by-Route Verification

## 1. Endpoint Inventory
35+ REST endpoints registered in FastAPI across 14 specialized routers:
- `/api/v1/system/*`: Health, metrics, live status
- `/api/v1/cases/*`: Case lifecycle, facts, scope versioning
- `/api/v1/agents/*`: Agent cluster telemetry, key revocation, commitments
- `/api/v1/evidence/*`: Passage citation, deduplication, tamper checks
- `/api/v1/forecasts/*`: Commit-reveal market participation
- `/api/v1/markets/*`: Prediction market creation, settlement, Brier scores
- `/api/v1/bounties/*`: Evidence bounties and escrow
- `/api/v1/audit/*`: Merkle root proofs and hash chains
- `/api/v1/ingestion/*`: Live source ingestion jobs

## 2. Complete Inventory Export
The comprehensive machine-readable inventory is recorded in `audit/real_data_transformation/api_route_inventory.json`.
