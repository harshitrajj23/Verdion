from typing import Any, Dict, List
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


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves metadata and status for a single specialized agent."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


@router.get("/executions/{execution_id}")
async def get_execution_trace(execution_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves execution trace, timing, status, and metadata for an agent execution job."""
    from backend.app.models.entities import AnalysisJob, AuditEvent
    job = await db.get(AnalysisJob, execution_id)
    if job:
        return {
            "execution_id": job.id,
            "case_id": job.case_id,
            "status": job.status,
            "retries": job.retries,
            "error_details": job.error_details,
            "result": job.result,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        }
    event = await db.get(AuditEvent, execution_id)
    if event:
        return {
            "execution_id": event.id,
            "case_id": event.case_id,
            "status": "COMPLETED",
            "actor": event.actor,
            "event_type": event.event_type,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None
        }
    raise HTTPException(status_code=404, detail=f"Execution trace '{execution_id}' not found")


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
