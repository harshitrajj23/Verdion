from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.market import (
    ForecastResponse,
    MarketCommitRequest,
    MarketCreateRequest,
    MarketResolveRequest,
    MarketResponse,
    MarketRevealRequest,
)
from backend.app.services.market_service import MarketService

router = APIRouter(prefix="/markets", tags=["Prediction Markets"])


@router.post("", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market(req: MarketCreateRequest, db: AsyncSession = Depends(get_db)):
    """Creates a new prediction market for an objective benchmark event (FR-031)."""
    return await MarketService.create_market(db, req)


@router.get("", response_model=List[MarketResponse])
async def list_markets(case_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    """Lists prediction markets, optionally filtered by case_id."""
    return await MarketService.get_all_markets(db, case_id)


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: str, db: AsyncSession = Depends(get_db)):
    """Reads market status, aggregate probability, disagreement variance, and reveals (FR-036)."""
    market = await MarketService.get_market(db, market_id)
    if not market:
        raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
    return market


@router.post("/{market_id}/commit", response_model=ForecastResponse)
async def commit_forecast(market_id: str, req: MarketCommitRequest, db: AsyncSession = Depends(get_db)):
    """Submits a commit hash H(chainId, marketId, agentId, prob, digest, nonce) before deadline (FR-033)."""
    return await MarketService.commit_forecast(db, market_id, req)


@router.post("/{market_id}/reveal", response_model=ForecastResponse)
async def reveal_forecast(market_id: str, req: MarketRevealRequest, db: AsyncSession = Depends(get_db)):
    """Reveals secret probability, nonce, and digest, cryptographically verified against commitment (FR-034)."""
    return await MarketService.reveal_forecast(db, market_id, req)


@router.post("/{market_id}/resolve", response_model=MarketResponse)
async def resolve_market(market_id: str, req: MarketResolveRequest, db: AsyncSession = Depends(get_db)):
    """Authorized evaluator proposes market outcome and benchmark reference (FR-038)."""
    return await MarketService.propose_resolution(db, market_id, req)


@router.post("/{market_id}/settle")
async def settle_market(market_id: str, db: AsyncSession = Depends(get_db)):
    """Settles market, computes Brier scores, and distributes simulated credits idempotently (FR-048, FR-052)."""
    return await MarketService.settle_market(db, market_id)
