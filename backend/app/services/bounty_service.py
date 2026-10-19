import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.crypto import compute_sha256_digest
from backend.app.core.errors import (
    InvalidScopeException,
    SettlementAlreadyDoneException,
    UnauthorizedResolutionException,
)
from backend.app.models.entities import (
    Agent,
    EvidenceBounty,
    EvidencePassage,
    EvidenceSubmission,
    ReputationRecord,
    Settlement,
    utcnow,
)
from backend.app.schemas.bounty import (
    BountyChallengeRequest,
    BountyCreateRequest,
    BountySettleRequest,
    EvidenceSubmissionRequest,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.blockchain_service import BlockchainService


class BountyService:
    @staticmethod
    async def create_bounty(
        db: AsyncSession,
        req: BountyCreateRequest,
        creator_address: str = "0xCoordinator"
    ) -> EvidenceBounty:
        bounty_id = f"bnty_{uuid.uuid4().hex[:10]}"
        creator = req.creator_address or creator_address

        bounty = EvidenceBounty(
            id=bounty_id,
            case_id=req.case_id,
            question=req.question,
            acceptance_criteria=req.acceptance_criteria,
            reward_amount=req.reward_amount,
            deadline=req.deadline,
            challenge_window_seconds=req.challenge_window_seconds,
            status="OPEN",  # Ready for evidence submissions
            contract_reference=settings.EVIDENCE_BOUNTY_ADDRESS,
            creator_address=creator,
            created_at=utcnow()
        )
        db.add(bounty)
        await db.flush()

        tx_info = BlockchainService.record_simulated_transaction(
            event_name="BountyCreated",
            contract_address=settings.EVIDENCE_BOUNTY_ADDRESS,
            sender_address=creator,
            case_id=req.case_id,
            data={"bounty_id": bounty_id, "reward": req.reward_amount}
        )

        await AuditService.log_event(
            db=db,
            case_id=req.case_id,
            event_type="BOUNTY_CREATED",
            actor=creator,
            payload={
                "bounty_id": bounty.id,
                "question": bounty.question,
                "reward_amount": bounty.reward_amount,
                "acceptance_criteria": bounty.acceptance_criteria
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(bounty)
        return bounty

    @staticmethod
    async def get_bounty(db: AsyncSession, bounty_id: str) -> Optional[EvidenceBounty]:
        return await db.get(EvidenceBounty, bounty_id)

    @staticmethod
    async def get_all_bounties(db: AsyncSession, case_id: Optional[str] = None) -> List[EvidenceBounty]:
        stmt = select(EvidenceBounty)
        if case_id:
            stmt = stmt.where(EvidenceBounty.case_id == case_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def submit_evidence(
        db: AsyncSession,
        bounty_id: str,
        req: EvidenceSubmissionRequest
    ) -> EvidenceSubmission:
        bounty = await db.get(EvidenceBounty, bounty_id)
        if not bounty:
            raise InvalidScopeException(f"Bounty {bounty_id} not found.")

        if bounty.status not in ["OPEN", "FUNDED"]:
            raise InvalidScopeException(f"Bounty {bounty_id} is not open for submissions (Status: {bounty.status}).")

        # Compute SHA-256 canonical digest (FR-026, FR-042)
        content_digest = compute_sha256_digest(req.content)

        # Anti-gaming duplicate detection check (FR-045)
        stmt = select(EvidenceSubmission).where(
            EvidenceSubmission.bounty_id == bounty_id,
            EvidenceSubmission.digest == content_digest
        )
        existing = await db.execute(stmt)
        if existing.scalars().first():
            raise InvalidScopeException("Duplicate evidence detected: identical content digest already submitted.")

        submission_id = f"sub_{uuid.uuid4().hex[:10]}"
        submission = EvidenceSubmission(
            id=submission_id,
            bounty_id=bounty_id,
            contributor_address=req.contributor_address,
            title=req.title,
            source_reference=req.source_reference,
            content=req.content,
            digest=content_digest,
            provenance=req.provenance or {
                "source": req.source_reference,
                "author": req.contributor_address,
                "timestamp": utcnow().isoformat()
            },
            status="SUBMITTED",
            submitted_at=utcnow()
        )
        db.add(submission)
        await db.flush()

        tx_info = BlockchainService.record_simulated_transaction(
            event_name="EvidenceSubmitted",
            contract_address=settings.EVIDENCE_BOUNTY_ADDRESS,
            sender_address=req.contributor_address,
            case_id=bounty.case_id,
            data={"bounty_id": bounty_id, "submission_id": submission_id, "digest": content_digest}
        )

        await AuditService.log_event(
            db=db,
            case_id=bounty.case_id,
            event_type="EVIDENCE_SUBMITTED",
            actor=req.contributor_address,
            payload={
                "bounty_id": bounty_id,
                "submission_id": submission_id,
                "title": req.title,
                "digest": content_digest
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def challenge_submission(
        db: AsyncSession,
        submission_id: str,
        req: BountyChallengeRequest
    ) -> EvidenceSubmission:
        submission = await db.get(EvidenceSubmission, submission_id)
        if not submission:
            raise InvalidScopeException(f"Submission {submission_id} not found.")

        bounty = await db.get(EvidenceBounty, submission.bounty_id)

        submission.status = "CHALLENGED"
        bounty.status = "CHALLENGE"
        await db.flush()

        tx_info = BlockchainService.record_simulated_transaction(
            event_name="BountyChallenged",
            contract_address=settings.EVIDENCE_BOUNTY_ADDRESS,
            sender_address=req.challenger_address,
            case_id=bounty.case_id,
            data={"submission_id": submission_id, "reason": req.reason}
        )

        await AuditService.log_event(
            db=db,
            case_id=bounty.case_id,
            event_type="BOUNTY_CHALLENGED",
            actor=req.challenger_address,
            payload={
                "bounty_id": bounty.id,
                "submission_id": submission_id,
                "reason": req.reason
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def settle_bounty(
        db: AsyncSession,
        bounty_id: str,
        req: BountySettleRequest
    ) -> Dict[str, Any]:
        """
        Settles bounty, releases reward credits to contributor,
        prevents duplicate settlement (FR-052).
        """
        bounty = await db.get(EvidenceBounty, bounty_id)
        if not bounty:
            raise InvalidScopeException(f"Bounty {bounty_id} not found.")

        if bounty.status == "SETTLED":
            raise SettlementAlreadyDoneException(f"Bounty {bounty_id} is already settled.")

        # Check authorized reviewer/evaluator role (FR-044)
        BlockchainService.assert_evaluator_role(req.reviewer_address)

        submission = await db.get(EvidenceSubmission, req.winning_submission_id)
        if not submission or submission.bounty_id != bounty_id:
            raise InvalidScopeException(f"Submission {req.winning_submission_id} not found for bounty {bounty_id}.")

        submission.status = "ACCEPTED"
        submission.review_reason = req.review_reason
        submission.reviewer_address = req.reviewer_address
        submission.reviewed_at = utcnow()

        bounty.winning_submission_id = submission.id
        bounty.status = "SETTLED"
        await db.flush()

        # Release reward to contributor wallet or agent
        reward_credits = bounty.reward_amount

        # Find contributor if agent
        stmt = select(Agent).where(Agent.wallet_address == submission.contributor_address)
        agent_res = await db.execute(stmt)
        agent = agent_res.scalars().first()
        if agent:
            score_before = agent.reputation_score
            agent.simulated_credits += reward_credits
            agent.reputation_score = round(min(100.0, agent.reputation_score + 3.0), 2)
            delta = round(agent.reputation_score - score_before, 2)

            rep_record = ReputationRecord(
                id=f"rep_{uuid.uuid4().hex[:10]}",
                agent_id=agent.id,
                delta=delta,
                score_before=score_before,
                score_after=agent.reputation_score,
                reason=f"Bounty settlement: Accepted submission {submission.id}",
                event_reference=bounty_id,
                timestamp=utcnow()
            )
            db.add(rep_record)

        tx_hash = BlockchainService.generate_tx_hash("BountySettled", bounty_id, submission.contributor_address)
        settlement = Settlement(
            id=f"stl_{uuid.uuid4().hex[:10]}",
            reference_type="BOUNTY",
            reference_id=bounty_id,
            participant_address=submission.contributor_address,
            score=1.0,
            reward=reward_credits,
            resolution_reference=f"Acceptance criteria: {bounty.acceptance_criteria[:60]}",
            tx_hash=tx_hash,
            created_at=utcnow()
        )
        db.add(settlement)

        await AuditService.log_event(
            db=db,
            case_id=bounty.case_id,
            event_type="BOUNTY_SETTLED",
            actor=req.reviewer_address,
            payload={
                "bounty_id": bounty_id,
                "winning_submission_id": submission.id,
                "winner_address": submission.contributor_address,
                "reward_amount": reward_credits,
                "review_reason": req.review_reason
            },
            tx_hash=tx_hash
        )

        await db.commit()
        await db.refresh(bounty)

        return {
            "bounty_id": bounty_id,
            "status": "SETTLED",
            "winner": submission.contributor_address,
            "reward_amount": reward_credits,
            "settlement_tx_hash": tx_hash
        }
