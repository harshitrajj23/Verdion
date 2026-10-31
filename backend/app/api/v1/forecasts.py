from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.crypto import compute_commitment_hash, verify_commitment_hash
from backend.app.core.database import get_db
from backend.app.models.entities import Agent, Forecast, PredictionMarket
from backend.app.schemas.market import ForecastResponse, MarketCommitRequest, MarketRevealRequest
from backend.app.services.forecast_evaluator import ForecastEvaluator
from backend.app.services.market_service import MarketService

router = APIRouter(tags=["Forecasting & Commitments"])


class ForecastCreateRequest(BaseModel):
    market_id: str = Field(..., description="Target prediction market ID")
    agent_id: str = Field(..., description="Agent submitting the forecast")
    probability: float = Field(..., ge=0.0, le=1.0, description="Predicted probability [0.0, 1.0]")
    evidence_digest: str = Field(..., description="SHA-256 digest of supporting evidence")
    nonce: str = Field(..., description="Secret 32-byte hexadecimal nonce")
    wallet_address: Optional[str] = Field(None, description="Optional agent wallet address")


class CommitmentCreateRequest(BaseModel):
    market_id: str = Field(..., description="Target prediction market ID")
    agent_id: str = Field(..., description="Agent submitting the commitment")
    commitment_hash: str = Field(..., description="6-field keccak256 commitment hash")
    wallet_address: Optional[str] = Field(None, description="Optional agent wallet address")


class CommitmentRevealRequest(BaseModel):
    agent_id: str = Field(..., description="Agent revealing the commitment")
    probability: float = Field(..., ge=0.0, le=1.0, description="Revealed probability [0.0, 1.0]")
    evidence_digest: str = Field(..., description="Revealed evidence digest")
    nonce: str = Field(..., description="Revealed secret nonce")
    wallet_address: Optional[str] = Field(None, description="Optional agent wallet address")


# -------------------------------------------------------------
# 1. Forecasts Endpoints
# -------------------------------------------------------------

@router.get("/forecasts", response_model=List[Dict[str, Any]])
async def list_forecasts(
    market_id: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Lists forecasts with commitment hash, reveal status, probability, and Brier score."""
    stmt = select(Forecast).limit(limit)
    if market_id:
        stmt = stmt.where(Forecast.market_id == market_id)
    if agent_id:
        stmt = stmt.where(Forecast.agent_id == agent_id)

    res = await db.execute(stmt)
    records = res.scalars().all()

    output = []
    for f in records:
        output.append({
            "id": f.id,
            "forecast_id": f.id,
            "market_id": f.market_id,
            "agent_id": f.agent_id,
            "commitment_hash": f.commitment_hash,
            "probability": f.probability,
            "evidence_digest": f.evidence_digest,
            "reveal_status": f.reveal_status,
            "brier_score": f.brier_score,
            "commit_tx_hash": f.commit_tx_hash,
            "reveal_tx_hash": f.reveal_tx_hash,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "revealed_at": f.revealed_at.isoformat() if f.revealed_at else None
        })
    return output


@router.post("/forecasts", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_forecast(req: ForecastCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Submits a forecast by generating the 6-field commitment hash and recording the commitment.
    keccak256(abi.encodePacked(chainId, marketId, agent, probBps, evidenceDigest, nonce))
    """
    agent = await db.get(Agent, req.agent_id)
    wallet = req.wallet_address or (agent.wallet_address if agent else "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")

    commit_hash = compute_commitment_hash(
        chain_id=settings.CHAIN_ID,
        market_id=req.market_id,
        agent_id=wallet,
        probability=req.probability,
        evidence_digest=req.evidence_digest,
        nonce=req.nonce,
        wallet_address=wallet
    )

    commit_req = MarketCommitRequest(
        agent_id=req.agent_id,
        commitment_hash=commit_hash,
        wallet_address=wallet
    )
    forecast = await MarketService.commit_forecast(db, req.market_id, commit_req)

    return {
        "id": forecast.id,
        "forecast_id": forecast.id,
        "market_id": forecast.market_id,
        "agent_id": forecast.agent_id,
        "commitment_hash": forecast.commitment_hash,
        "reveal_status": forecast.reveal_status,
        "created_at": forecast.created_at.isoformat() if forecast.created_at else None
    }


@router.get("/forecasts/{forecast_id}", response_model=Dict[str, Any])
async def get_forecast(forecast_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a single forecast record by ID."""
    forecast = await db.get(Forecast, forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail=f"Forecast '{forecast_id}' not found")

    return {
        "id": forecast.id,
        "forecast_id": forecast.id,
        "market_id": forecast.market_id,
        "agent_id": forecast.agent_id,
        "commitment_hash": forecast.commitment_hash,
        "probability": forecast.probability,
        "evidence_digest": forecast.evidence_digest,
        "reveal_status": forecast.reveal_status,
        "brier_score": forecast.brier_score,
        "commit_tx_hash": forecast.commit_tx_hash,
        "reveal_tx_hash": forecast.reveal_tx_hash,
        "created_at": forecast.created_at.isoformat() if forecast.created_at else None,
        "revealed_at": forecast.revealed_at.isoformat() if forecast.revealed_at else None
    }


@router.get("/forecasts/{forecast_id}/metrics", response_model=Dict[str, Any])
async def get_forecast_metrics(forecast_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves scoring and proper-scoring evaluation metrics for a forecast."""
    forecast = await db.get(Forecast, forecast_id)
    if not forecast:
        raise HTTPException(status_code=404, detail=f"Forecast '{forecast_id}' not found")

    market = await db.get(PredictionMarket, forecast.market_id)
    return {
        "forecast_id": forecast.id,
        "market_id": forecast.market_id,
        "agent_id": forecast.agent_id,
        "probability": forecast.probability,
        "reveal_status": forecast.reveal_status,
        "brier_score": forecast.brier_score,
        "scoring_rule": "PROPER_BRIER_SCORE_HALF_QUADRATIC",
        "market_status": market.status if market else "UNKNOWN",
        "market_outcome": market.proposed_outcome if market else None,
        "is_settled": (market.status == "SETTLED") if market else False
    }


# -------------------------------------------------------------
# 2. Commitments Endpoints
# -------------------------------------------------------------

@router.get("/commitments", response_model=List[Dict[str, Any]])
async def list_commitments(
    market_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Lists on-chain forecast commitments."""
    return await list_forecasts(market_id=market_id, limit=limit, db=db)


@router.post("/commitments", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_commitment(req: CommitmentCreateRequest, db: AsyncSession = Depends(get_db)):
    """Submits a raw keccak256 commitment hash to a prediction market."""
    commit_req = MarketCommitRequest(
        agent_id=req.agent_id,
        commitment_hash=req.commitment_hash,
        wallet_address=req.wallet_address
    )
    forecast = await MarketService.commit_forecast(db, req.market_id, commit_req)
    return {
        "commitment_id": forecast.id,
        "id": forecast.id,
        "market_id": forecast.market_id,
        "agent_id": forecast.agent_id,
        "commitment_hash": forecast.commitment_hash,
        "status": forecast.reveal_status
    }


@router.get("/commitments/{commitment_id}", response_model=Dict[str, Any])
async def get_commitment(commitment_id: str, db: AsyncSession = Depends(get_db)):
    """Reads a commitment by its ID."""
    return await get_forecast(commitment_id, db)


@router.post("/commitments/{commitment_id}/reveal", response_model=Dict[str, Any])
async def reveal_commitment(
    commitment_id: str,
    req: CommitmentRevealRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reveals the underlying probability, evidence digest, and nonce for a commitment.
    Verifies 6-field keccak256 parity with Solidity before accepting.
    """
    forecast = await db.get(Forecast, commitment_id)
    if not forecast:
        raise HTTPException(status_code=404, detail=f"Commitment '{commitment_id}' not found")

    reveal_req = MarketRevealRequest(
        agent_id=req.agent_id,
        probability=req.probability,
        evidence_digest=req.evidence_digest,
        nonce=req.nonce,
        wallet_address=req.wallet_address
    )

    revealed_fc = await MarketService.reveal_forecast(db, forecast.market_id, reveal_req)
    return {
        "commitment_id": revealed_fc.id,
        "id": revealed_fc.id,
        "market_id": revealed_fc.market_id,
        "agent_id": revealed_fc.agent_id,
        "probability": revealed_fc.probability,
        "evidence_digest": revealed_fc.evidence_digest,
        "reveal_status": revealed_fc.reveal_status,
        "revealed_at": revealed_fc.revealed_at.isoformat() if revealed_fc.revealed_at else None
    }


@router.get("/commitments/{commitment_id}/verify", response_model=Dict[str, Any])
async def verify_commitment_record(commitment_id: str, db: AsyncSession = Depends(get_db)):
    """Independently verifies that a revealed commitment hash matches its claimed fields."""
    forecast = await db.get(Forecast, commitment_id)
    if not forecast:
        raise HTTPException(status_code=404, detail=f"Commitment '{commitment_id}' not found")

    if forecast.reveal_status != "REVEALED":
        return {
            "commitment_id": commitment_id,
            "status": forecast.reveal_status,
            "is_verified": False,
            "message": "Commitment is not yet revealed or is invalid"
        }

    agent = await db.get(Agent, forecast.agent_id)
    wallet = agent.wallet_address if agent else "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

    is_valid = verify_commitment_hash(
        expected_hash=forecast.commitment_hash,
        chain_id=settings.CHAIN_ID,
        market_id=forecast.market_id,
        agent_id=wallet,
        probability=forecast.probability,
        evidence_digest=forecast.evidence_digest,
        nonce=forecast.nonce,
        wallet_address=wallet
    )

    return {
        "commitment_id": commitment_id,
        "market_id": forecast.market_id,
        "agent_id": forecast.agent_id,
        "wallet_address": wallet,
        "chain_id": settings.CHAIN_ID,
        "stored_hash": forecast.commitment_hash,
        "revealed_probability": forecast.probability,
        "revealed_digest": forecast.evidence_digest,
        "revealed_nonce": forecast.nonce,
        "is_verified": is_valid,
        "verification_result": "MATCH" if is_valid else "MISMATCH"
    }

