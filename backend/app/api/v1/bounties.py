from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.schemas.bounty import (
    BountyChallengeRequest,
    BountyCreateRequest,
    BountyResponse,
    BountySettleRequest,
    EvidenceSubmissionRequest,
    EvidenceSubmissionResponse,
)
from backend.app.services.bounty_service import BountyService

router = APIRouter(prefix="", tags=["Evidence Bounties"])


@router.post("/bounties", response_model=BountyResponse, status_code=status.HTTP_201_CREATED)
async def create_bounty(req: BountyCreateRequest, db: AsyncSession = Depends(get_db)):
    """Creates a targeted evidence research bounty funded with simulated credits (FR-040)."""
    return await BountyService.create_bounty(db, req)


@router.get("/bounties", response_model=List[BountyResponse])
async def list_bounties(case_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    """Lists research bounties, optionally filtered by case."""
    return await BountyService.get_all_bounties(db, case_id)


@router.get("/bounties/{bounty_id}", response_model=BountyResponse)
async def get_bounty(bounty_id: str, db: AsyncSession = Depends(get_db)):
    """Reads bounty status, criteria, reward, and submissions (FR-043)."""
    bounty = await BountyService.get_bounty(db, bounty_id)
    if not bounty:
        raise HTTPException(status_code=404, detail=f"Bounty {bounty_id} not found")
    return bounty


@router.post("/bounties/{bounty_id}/submissions", response_model=EvidenceSubmissionResponse)
async def submit_evidence(bounty_id: str, req: EvidenceSubmissionRequest, db: AsyncSession = Depends(get_db)):
    """Submits evidence with SHA256 digest and checks for duplicate submissions (FR-042, FR-045)."""
    return await BountyService.submit_evidence(db, bounty_id, req)


@router.post("/submissions/{submission_id}/challenge", response_model=EvidenceSubmissionResponse)
async def challenge_submission(submission_id: str, req: BountyChallengeRequest, db: AsyncSession = Depends(get_db)):
    """Challenges a submission decision within the configured challenge window (FR-046)."""
    return await BountyService.challenge_submission(db, submission_id, req)


@router.post("/bounties/{bounty_id}/settle")
async def settle_bounty(bounty_id: str, req: BountySettleRequest, db: AsyncSession = Depends(get_db)):
    """Authorizes reward release and settles simulated credits idempotently (FR-044, FR-052)."""
    return await BountyService.settle_bounty(db, bounty_id, req)
