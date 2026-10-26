from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.core.errors import VeridionAPIException
from backend.app.services.agent_service import AgentService
from backend.app.services.retrieval_service import RetrievalService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables, corpus, and agents
    await init_db()
    async with AsyncSessionLocal() as session:
        await RetrievalService.initialize_corpus(session)
        await AgentService.initialize_agents(session)
    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VERIDION Decentralized Legal Intelligence Protocol - API & Reasoning Backend",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

from backend.app.core.middleware import IdempotencyMiddleware, TraceIdMiddleware

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Idempotency and Trace ID Middlewares (§15.1, §20.2)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(TraceIdMiddleware)


@app.exception_handler(VeridionAPIException)
async def veridion_exception_handler(request: Request, exc: VeridionAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


# Attach API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "veridion-backend",
        "version": settings.VERSION,
        "chain_id": settings.CHAIN_ID,
        "database": "connected"
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "protocol": "VERIDION Decentralized Legal Intelligence Protocol",
        "motto": "Reason. Predict. Verify.",
        "documentation": f"{settings.API_V1_STR}/docs",
        "version": settings.VERSION
    }
