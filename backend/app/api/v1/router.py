from fastapi import APIRouter
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.bounties import router as bounties_router
from backend.app.api.v1.cases import router as cases_router
from backend.app.api.v1.decisions import router as decisions_router
from backend.app.api.v1.demo import router as demo_router
from backend.app.api.v1.evaluations import router as evaluations_router
from backend.app.api.v1.evidence import router as evidence_router
from backend.app.api.v1.forecasts import router as forecasts_router
from backend.app.api.v1.ingestion import router as ingestion_router
from backend.app.api.v1.integrations import router as integrations_router
from backend.app.api.v1.markets import router as markets_router
from backend.app.api.v1.sources import router as sources_router
from backend.app.api.v1.system import router as system_router

api_router = APIRouter()

# Core System & Capabilities
api_router.include_router(system_router)

# Cases & Decisions
api_router.include_router(cases_router)
api_router.include_router(decisions_router)

# Sources & Evidence
api_router.include_router(sources_router)
api_router.include_router(evidence_router)

# Multi-Agent Platform
api_router.include_router(agents_router)

# Forecasting, Prediction Markets & Commitments
api_router.include_router(forecasts_router)
api_router.include_router(markets_router)
api_router.include_router(bounties_router)

# Audit Trail & Verification
api_router.include_router(audit_router)

# Benchmarks, Ingestion, Integrations & Showcase Demo
api_router.include_router(evaluations_router)
api_router.include_router(ingestion_router)
api_router.include_router(integrations_router)
api_router.include_router(demo_router)
