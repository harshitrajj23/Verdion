from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.entities import Agent, ReputationRecord
from backend.app.schemas.agent import (
    AgentReputationResponse,
    AgentResponse,
    ReputationRecordResponse,
)
from backend.app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    """Lists all registered protocol agents and their metrics."""
    return await AgentService.get_all_agents(db)


@router.get("/{agent_id}/reputation", response_model=AgentReputationResponse)
async def get_agent_reputation(agent_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns empirical agent calibration metrics, Brier score,
    and safeguards against small-sample reputation inflation (FR-047, FR-049).
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    is_small = agent.sample_count < 10
    # Damping weight for small sample sizes
    weight = round(min(1.0, agent.sample_count / 10.0), 2)

    return AgentReputationResponse(
        agent_id=agent.id,
        wallet_address=agent.wallet_address,
        role=agent.role,
        reputation_score=agent.reputation_score,
        brier_score=agent.brier_score,
        sample_count=agent.sample_count,
        simulated_credits=agent.simulated_credits,
        scoring_version="brier_v1",
        is_small_sample=is_small,
        reputation_weight=weight
    )


@router.get("/{agent_id}/reputation/history", response_model=List[ReputationRecordResponse])
async def get_agent_reputation_history(agent_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the chronological history of reputation updates for an agent.
    """
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    stmt = select(ReputationRecord).where(
        ReputationRecord.agent_id == agent_id
    ).order_by(ReputationRecord.timestamp.desc())
    res = await db.execute(stmt)
    records = res.scalars().all()
    return records
