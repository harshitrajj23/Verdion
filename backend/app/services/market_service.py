import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.crypto import (
    compute_brier_score,
    compute_variance,
    verify_commitment_hash,
)
from backend.app.core.errors import (
    CommitmentMismatchException,
    InvalidForecastException,
    MarketClosedException,
    SettlementAlreadyDoneException,
    UnauthorizedResolutionException,
)
from backend.app.models.entities import (
    Agent,
    Forecast,
    PredictionMarket,
    ReputationRecord,
    Settlement,
    utcnow,
)
from backend.app.schemas.market import (
    MarketCommitRequest,
    MarketCreateRequest,
    MarketResolveRequest,
    MarketRevealRequest,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.blockchain_service import BlockchainService


class MarketService:
    @staticmethod
    async def create_market(
        db: AsyncSession,
        req: MarketCreateRequest,
        creator_address: str = "0xCreator"
    ) -> PredictionMarket:
        market_id = f"mkt_{uuid.uuid4().hex[:10]}"
        evaluator = req.evaluator_address or settings.EVALUATOR_ADDRESS

        market = PredictionMarket(
            id=market_id,
            case_id=req.case_id,
            case_version=1,
            question=req.question,
            outcome_definition=req.outcome_definition,
            resolution_method=req.resolution_method,
            rubric_version=req.rubric_version,
            commit_deadline=req.commit_deadline,
            reveal_deadline=req.reveal_deadline,
            resolution_deadline=req.resolution_deadline,
            challenge_window_seconds=req.challenge_window_seconds,
            scoring_version="brier_v1",
            void_criteria=req.void_criteria,
            status="PUBLISHED",  # Published ready for commitments
            contract_address=settings.PREDICTION_MARKET_ADDRESS,
            evaluator_address=evaluator,
            aggregate_probability=0.0,
            disagreement_variance=0.0,
            sample_size=0,
            created_at=utcnow()
        )
        db.add(market)
        await db.flush()

        tx_info = BlockchainService.record_simulated_transaction(
            event_name="MarketPublished",
            contract_address=settings.PREDICTION_MARKET_ADDRESS,
            sender_address=creator_address,
            case_id=req.case_id,
            data={"market_id": market_id, "question": market.question}
        )

        await AuditService.log_event(
            db=db,
            case_id=req.case_id,
            event_type="MARKET_CREATED",
            actor=creator_address,
            payload={
                "market_id": market.id,
                "question": market.question,
                "commit_deadline": market.commit_deadline.isoformat(),
                "evaluator_address": market.evaluator_address
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(market)
        return market

    @staticmethod
    async def get_market(db: AsyncSession, market_id: str) -> Optional[PredictionMarket]:
        return await db.get(PredictionMarket, market_id)

    @staticmethod
    async def get_all_markets(db: AsyncSession, case_id: Optional[str] = None) -> List[PredictionMarket]:
        stmt = select(PredictionMarket)
        if case_id:
            stmt = stmt.where(PredictionMarket.case_id == case_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def commit_forecast(
        db: AsyncSession,
        market_id: str,
        req: MarketCommitRequest,
        sender_address: str = "0xAgent"
    ) -> Forecast:
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market {market_id} not found.")

        # Deadline check (FR-033)
        if market.status not in ["PUBLISHED", "DRAFT"]:
            raise MarketClosedException(f"Commitments closed for market {market_id} (Status: {market.status})")

        # One commitment per agent/market check
        stmt = select(Forecast).where(Forecast.market_id == market_id, Forecast.agent_id == req.agent_id)
        existing = await db.execute(stmt)
        if existing.scalars().first():
            raise InvalidForecastException(f"Agent {req.agent_id} has already committed to market {market_id}.")

        forecast_id = f"fc_{uuid.uuid4().hex[:10]}"
        tx_info = BlockchainService.record_simulated_transaction(
            event_name="ForecastCommitted",
            contract_address=market.contract_address,
            sender_address=sender_address,
            case_id=market.case_id,
            data={"market_id": market_id, "agent_id": req.agent_id, "hash": req.commitment_hash}
        )

        forecast = Forecast(
            id=forecast_id,
            market_id=market_id,
            agent_id=req.agent_id,
            commitment_hash=req.commitment_hash,
            reveal_status="COMMITTED",
            commit_tx_hash=tx_info["transaction_hash"],
            created_at=utcnow()
        )
        db.add(forecast)
        await db.flush()

        await AuditService.log_event(
            db=db,
            case_id=market.case_id,
            event_type="FORECAST_COMMITTED",
            actor=req.agent_id,
            payload={
                "market_id": market_id,
                "agent_id": req.agent_id,
                "commitment_hash": req.commitment_hash
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(forecast)
        return forecast

    @staticmethod
    async def reveal_forecast(
        db: AsyncSession,
        market_id: str,
        req: MarketRevealRequest,
        sender_address: str = "0xAgent"
    ) -> Forecast:
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market {market_id} not found.")

        if not (0.0 <= req.probability <= 1.0):
            raise InvalidForecastException(f"Probability must be in range [0, 1], got {req.probability}")

        # Fetch commitment
        stmt = select(Forecast).where(Forecast.market_id == market_id, Forecast.agent_id == req.agent_id)
        res = await db.execute(stmt)
        forecast = res.scalars().first()
        if not forecast:
            raise InvalidForecastException(f"No prior commitment found for agent {req.agent_id} in market {market_id}.")

        if forecast.reveal_status == "REVEALED":
            raise InvalidForecastException(f"Forecast for agent {req.agent_id} has already been revealed.")

        # Cryptographic verification against commitment hash (FR-034)
        BlockchainService.verify_agent_reveal(
            expected_hash=forecast.commitment_hash,
            chain_id=settings.CHAIN_ID,
            market_id=market_id,
            agent_id=req.agent_id,
            probability=req.probability,
            evidence_digest=req.evidence_digest,
            nonce=req.nonce
        )

        tx_info = BlockchainService.record_simulated_transaction(
            event_name="ForecastRevealed",
            contract_address=market.contract_address,
            sender_address=sender_address,
            case_id=market.case_id,
            data={"market_id": market_id, "agent_id": req.agent_id, "probability": req.probability}
        )

        forecast.probability = req.probability
        forecast.evidence_digest = req.evidence_digest
        forecast.nonce = req.nonce
        forecast.reveal_status = "REVEALED"
        forecast.reveal_tx_hash = tx_info["transaction_hash"]
        forecast.revealed_at = utcnow()
        await db.flush()

        # Update market aggregation deterministically (FR-035)
        stmt_revealed = select(Forecast).where(
            Forecast.market_id == market_id,
            Forecast.reveal_status == "REVEALED"
        )
        res_all = await db.execute(stmt_revealed)
        revealed_forecasts = res_all.scalars().all()

        probs = [f.probability for f in revealed_forecasts if f.probability is not None]
        if probs:
            market.sample_size = len(probs)
            market.aggregate_probability = round(sum(probs) / len(probs), 4)
            market.disagreement_variance = compute_variance(probs)

        market.status = "REVEAL"
        await db.flush()

        await AuditService.log_event(
            db=db,
            case_id=market.case_id,
            event_type="FORECAST_REVEALED",
            actor=req.agent_id,
            payload={
                "market_id": market_id,
                "agent_id": req.agent_id,
                "probability": req.probability,
                "aggregate_probability": market.aggregate_probability,
                "disagreement_variance": market.disagreement_variance
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(forecast)
        return forecast

    @staticmethod
    async def propose_resolution(
        db: AsyncSession,
        market_id: str,
        req: MarketResolveRequest
    ) -> PredictionMarket:
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market {market_id} not found.")

        # Check authorized evaluator role (FR-038)
        BlockchainService.assert_evaluator_role(req.evaluator_address)

        market.proposed_outcome = req.proposed_outcome
        market.resolution_reference = req.resolution_reference
        market.status = "RESOLUTION_PROPOSED"
        await db.flush()

        tx_info = BlockchainService.record_simulated_transaction(
            event_name="ResolutionProposed",
            contract_address=market.contract_address,
            sender_address=req.evaluator_address,
            case_id=market.case_id,
            data={"market_id": market_id, "proposed_outcome": req.proposed_outcome}
        )

        await AuditService.log_event(
            db=db,
            case_id=market.case_id,
            event_type="RESOLUTION_PROPOSED",
            actor=req.evaluator_address,
            payload={
                "market_id": market_id,
                "proposed_outcome": req.proposed_outcome,
                "resolution_reference": req.resolution_reference
            },
            tx_hash=tx_info["transaction_hash"]
        )

        await db.commit()
        await db.refresh(market)
        return market

    @staticmethod
    async def settle_market(
        db: AsyncSession,
        market_id: str,
        settler_address: str = "0xEvaluator"
    ) -> Dict[str, Any]:
        """
        Settles market, scores forecasts using Brier score (PRD 9.5),
        updates agent reputation and credits, prevents duplicate settlement.
        """
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market {market_id} not found.")

        if market.status == "SETTLED":
            raise SettlementAlreadyDoneException(f"Market {market_id} is already settled.")

        if market.proposed_outcome is None:
            raise InvalidForecastException(f"Cannot settle market without proposed resolution outcome.")

        # Fetch revealed forecasts
        stmt = select(Forecast).where(
            Forecast.market_id == market_id,
            Forecast.reveal_status == "REVEALED"
        )
        res = await db.execute(stmt)
        forecasts = res.scalars().all()

        outcome = market.proposed_outcome
        settlement_results = []

        for fc in forecasts:
            if fc.probability is not None:
                # Brier score for single binary outcome: (p - y)^2
                bs = round((fc.probability - outcome) ** 2, 4)
                fc.brier_score = bs

                # Fetch agent and update reputation and simulated credits
                agent = await db.get(Agent, fc.agent_id)
                reward = 0.0
                if agent:
                    score_before = agent.reputation_score
                    # Good calibration (lower Brier score) earns rewards
                    if bs < 0.10:
                        reward = 150.0
                        agent.reputation_score = round(min(100.0, agent.reputation_score + 2.0), 2)
                    elif bs < 0.25:
                        reward = 75.0
                        agent.reputation_score = round(min(100.0, agent.reputation_score + 0.5), 2)
                    else:
                        reward = 10.0
                        agent.reputation_score = round(max(0.0, agent.reputation_score - 1.5), 2)

                    delta = round(agent.reputation_score - score_before, 2)
                    agent.simulated_credits += reward
                    agent.sample_count += 1
                    # Running brier score average
                    agent.brier_score = round(
                        (agent.brier_score * (agent.sample_count - 1) + bs) / agent.sample_count, 4
                    )

                    rep_record = ReputationRecord(
                        id=f"rep_{uuid.uuid4().hex[:10]}",
                        agent_id=agent.id,
                        delta=delta,
                        score_before=score_before,
                        score_after=agent.reputation_score,
                        reason=f"Market settlement: Brier score {bs}",
                        event_reference=market_id,
                        timestamp=utcnow()
                    )
                    db.add(rep_record)

                tx_hash = BlockchainService.generate_tx_hash("MarketSettled", market_id, fc.agent_id)
                settlement = Settlement(
                    id=f"stl_{uuid.uuid4().hex[:10]}",
                    reference_type="MARKET",
                    reference_id=market_id,
                    participant_address=agent.wallet_address if agent else "0xUnknown",
                    score=bs,
                    reward=reward,
                    resolution_reference=market.resolution_reference or "evaluator_benchmark",
                    tx_hash=tx_hash,
                    created_at=utcnow()
                )
                db.add(settlement)

                settlement_results.append({
                    "agent_id": fc.agent_id,
                    "probability": fc.probability,
                    "outcome": outcome,
                    "brier_score": bs,
                    "reward": reward,
                    "tx_hash": tx_hash
                })

        market.status = "SETTLED"
        await db.flush()

        await AuditService.log_event(
            db=db,
            case_id=market.case_id,
            event_type="MARKET_SETTLED",
            actor=settler_address,
            payload={
                "market_id": market_id,
                "outcome": outcome,
                "participants_settled": len(settlement_results),
                "aggregate_probability": market.aggregate_probability
            }
        )

        await db.commit()
        await db.refresh(market)
        return {
            "market_id": market_id,
            "status": "SETTLED",
            "outcome": outcome,
            "settlements": settlement_results
        }
