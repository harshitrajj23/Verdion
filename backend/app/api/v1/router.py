from fastapi import APIRouter
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.bounties import router as bounties_router
from backend.app.api.v1.cases import router as cases_router
from backend.app.api.v1.demo import router as demo_router
from backend.app.api.v1.evaluations import router as evaluations_router
from backend.app.api.v1.markets import router as markets_router
from backend.app.api.v1.sources import router as sources_router

api_router = APIRouter()

api_router.include_router(cases_router)
api_router.include_router(sources_router)
api_router.include_router(markets_router)
api_router.include_router(bounties_router)
api_router.include_router(agents_router)
api_router.include_router(audit_router)
api_router.include_router(evaluations_router)
api_router.include_router(demo_router)
