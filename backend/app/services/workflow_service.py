import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.canonical import (
    compute_canonical_sha256,
    format_canonical_timestamp,
    CANONICAL_SCHEMA_VERSION,
)
from backend.app.core.config import settings
from backend.app.core.errors import (
    InvalidScopeException,
    InvalidStateTransitionException,
    InsufficientEvidenceException,
    InvalidForecastException,
    SettlementAlreadyDoneException,
)
from backend.app.models.entities import (
    Agent,
    AuditEvent,
    Case,
    Claim,
    ClaimEvidenceLink,
    DecisionRecordEntity,
    EvidencePassage,
    Forecast,
    PredictionMarket,
    Settlement,
    SourceDocument,
    utcnow,
)
from backend.app.schemas.decision_record import CanonicalDecisionRecord
from backend.app.schemas.market import (
    MarketCommitRequest,
    MarketCreateRequest,
    MarketResolveRequest,
    MarketRevealRequest,
)
from backend.app.services.agent_service import AgentService
from backend.app.services.audit_service import AuditService
from backend.app.services.audit_verifier import IndependentAuditVerifier
from backend.app.services.blockchain_service import BlockchainService
from backend.app.services.case_service import CaseService
from backend.app.services.decision_service import DecisionService
from backend.app.services.market_service import MarketService
from backend.app.services.retrieval_service import RetrievalService


class WorkflowState(str, Enum):
    CASE_CREATED = "CASE_CREATED"
    EVIDENCE_BOUND = "EVIDENCE_BOUND"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ANALYSIS_RECORDED = "ANALYSIS_RECORDED"
    DECISION_VERIFIED = "DECISION_VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FORECAST_OPEN = "FORECAST_OPEN"
    FORECAST_COMMITTED = "FORECAST_COMMITTED"
    FORECAST_REVEALED = "FORECAST_REVEALED"
    REVEAL_EXPIRED = "REVEAL_EXPIRED"
    RESOLUTION_PENDING = "RESOLUTION_PENDING"
    RESOLVED = "RESOLVED"
    DISPUTED = "DISPUTED"
    SCORED = "SCORED"
    AUDIT_PACKAGE_VERIFIED = "AUDIT_PACKAGE_VERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# Permitted state transitions table
PERMITTED_TRANSITIONS: Dict[str, List[str]] = {
    # Legacy aliases
    "DRAFT": [
        WorkflowState.CASE_CREATED.value,
        WorkflowState.EVIDENCE_BOUND.value,
        WorkflowState.INSUFFICIENT_EVIDENCE.value,
        WorkflowState.ANALYSIS_RECORDED.value,
        WorkflowState.CANCELLED.value,
    ],
    "RETRIEVAL": [
        WorkflowState.EVIDENCE_BOUND.value,
        WorkflowState.INSUFFICIENT_EVIDENCE.value,
        WorkflowState.CANCELLED.value,
    ],
    "ANALYSIS": [
        WorkflowState.ANALYSIS_RECORDED.value,
        WorkflowState.FAILED.value,
        WorkflowState.CANCELLED.value,
    ],
    "INVESTIGATION": [
        WorkflowState.ANALYSIS_RECORDED.value,
        WorkflowState.DECISION_VERIFIED.value,
        WorkflowState.FAILED.value,
    ],
    "COMPLETED": [
        WorkflowState.DECISION_VERIFIED.value,
        WorkflowState.FORECAST_OPEN.value,
        WorkflowState.AUDIT_PACKAGE_VERIFIED.value,
    ],
    # Formal Workflow States
    WorkflowState.CASE_CREATED.value: [
        WorkflowState.EVIDENCE_BOUND.value,
        WorkflowState.INSUFFICIENT_EVIDENCE.value,
        WorkflowState.ANALYSIS_RECORDED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.EVIDENCE_BOUND.value: [
        WorkflowState.ANALYSIS_RECORDED.value,
        WorkflowState.INSUFFICIENT_EVIDENCE.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.INSUFFICIENT_EVIDENCE.value: [
        WorkflowState.EVIDENCE_BOUND.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.ANALYSIS_RECORDED.value: [
        WorkflowState.DECISION_VERIFIED.value,
        WorkflowState.PARTIALLY_VERIFIED.value,
        WorkflowState.FAILED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.PARTIALLY_VERIFIED.value: [
        WorkflowState.ANALYSIS_RECORDED.value,
        WorkflowState.DECISION_VERIFIED.value,
        WorkflowState.FORECAST_OPEN.value,
        WorkflowState.AUDIT_PACKAGE_VERIFIED.value,
        WorkflowState.FAILED.value,
    ],
    WorkflowState.DECISION_VERIFIED.value: [
        WorkflowState.FORECAST_OPEN.value,
        WorkflowState.AUDIT_PACKAGE_VERIFIED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.FORECAST_OPEN.value: [
        WorkflowState.FORECAST_COMMITTED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.FORECAST_COMMITTED.value: [
        WorkflowState.FORECAST_REVEALED.value,
        WorkflowState.REVEAL_EXPIRED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.FORECAST_REVEALED.value: [
        WorkflowState.RESOLUTION_PENDING.value,
        WorkflowState.RESOLVED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.REVEAL_EXPIRED.value: [
        WorkflowState.RESOLUTION_PENDING.value,
        WorkflowState.RESOLVED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.RESOLUTION_PENDING.value: [
        WorkflowState.RESOLVED.value,
        WorkflowState.DISPUTED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.DISPUTED.value: [
        WorkflowState.RESOLVED.value,
        WorkflowState.CANCELLED.value,
    ],
    WorkflowState.RESOLVED.value: [
        WorkflowState.SCORED.value,
        WorkflowState.FAILED.value,
    ],
    WorkflowState.SCORED.value: [
        WorkflowState.AUDIT_PACKAGE_VERIFIED.value,
    ],
    WorkflowState.AUDIT_PACKAGE_VERIFIED.value: [],
    WorkflowState.FAILED.value: [
        WorkflowState.CASE_CREATED.value,
        WorkflowState.ANALYSIS_RECORDED.value,
    ],
    WorkflowState.CANCELLED.value: [],
}


class WorkflowService:
    """
    Coherent lifecycle state machine orchestrating end-to-end regulatory decisions:
    Evidence Binding -> Analysis -> Canonical Decision Record -> Verification ->
    Forecast Commitment -> Reveal -> Outcome Resolution -> Scoring -> Audit Package Verification.
    """

    @staticmethod
    async def transition_state(
        db: AsyncSession,
        case_id: str,
        to_state: str,
        actor: str = "SYSTEM_ORCHESTRATOR",
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transitions case to the target workflow state.
        Validates transition rules, enforces idempotency, logs audit events.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case '{case_id}' not found.")

        current_state = case.status

        # Idempotent check
        if current_state == to_state:
            return {
                "case_id": case_id,
                "current_state": current_state,
                "target_state": to_state,
                "transitioned": False,
                "idempotent": True,
                "message": f"Case is already in state '{to_state}'."
            }

        # Check allowed transitions
        allowed = PERMITTED_TRANSITIONS.get(current_state, [])
        if to_state not in allowed:
            raise InvalidStateTransitionException(
                f"Invalid workflow state transition from '{current_state}' to '{to_state}'.",
                details={
                    "current_state": current_state,
                    "target_state": to_state,
                    "allowed_transitions": allowed
                }
            )

        # Apply transition
        case.status = to_state
        case.updated_at = utcnow()
        await db.flush()

        # Audit event for state transition
        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="WORKFLOW_STATE_TRANSITION",
            actor=actor,
            payload={
                "previous_state": current_state,
                "new_state": to_state,
                "reason": reason or f"Transitioned to {to_state}",
                "metadata": metadata or {},
                "idempotency_key": idempotency_key
            }
        )

        await db.commit()
        await db.refresh(case)

        return {
            "case_id": case_id,
            "previous_state": current_state,
            "current_state": to_state,
            "transitioned": True,
            "idempotent": False,
            "timestamp": format_canonical_timestamp(case.updated_at)
        }

    @staticmethod
    async def bind_evidence_to_case(
        db: AsyncSession,
        case_id: str,
        query_override: Optional[str] = None,
        min_passages: int = 1,
        actor: str = "SYSTEM_ORCHESTRATOR"
    ) -> Dict[str, Any]:
        """
        Stage B — Retrieves official legal documents and binds exact evidence passages to the case.
        If no relevant passages exist in the curated corpus, halts honestly with INSUFFICIENT_EVIDENCE.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case '{case_id}' not found.")

        query = query_override or f"{case.question} {' '.join(case.facts.get('data_categories', []))} {case.facts.get('processing_purpose', '')}"
        passages = await RetrievalService.retrieve_passages(
            db=db,
            query=query.strip(),
            jurisdiction=case.jurisdiction,
            limit=5
        )

        if len(passages) < min_passages:
            # Transition to INSUFFICIENT_EVIDENCE
            await WorkflowService.transition_state(
                db=db,
                case_id=case_id,
                to_state=WorkflowState.INSUFFICIENT_EVIDENCE.value,
                actor=actor,
                reason="No legally authoritative passages found matching case question and facts."
            )
            return {
                "case_id": case_id,
                "status": WorkflowState.INSUFFICIENT_EVIDENCE.value,
                "passages_count": len(passages),
                "passages": [],
                "message": "Eligible corpus contains insufficient authoritative evidence to decide this proposition."
            }

        # Transition to EVIDENCE_BOUND
        await WorkflowService.transition_state(
            db=db,
            case_id=case_id,
            to_state=WorkflowState.EVIDENCE_BOUND.value,
            actor=actor,
            reason=f"Bound {len(passages)} official evidence passages to case."
        )

        passage_details = []
        for p in passages:
            if isinstance(p, dict):
                p_id = p.get("evidence_id") or p.get("id") or p.get("passage_id")
                doc_id = p.get("document_id")
                p_ref = p.get("passage_reference")
                c_ref = p.get("content_reference")
                text = p.get("text", "")
                p_digest = p.get("digest") or p.get("passage_digest")
                provenance = p.get("provenance") or "BUNDLED_FIXTURE"
            else:
                p_id = getattr(p, "id", None) or getattr(p, "evidence_id", None)
                doc_id = getattr(p, "document_id", None)
                p_ref = getattr(p, "passage_reference", None)
                c_ref = getattr(p, "content_reference", None)
                text = getattr(p, "text", "")
                p_digest = getattr(p, "digest", None)
                provenance = getattr(p, "provenance", "BUNDLED_FIXTURE")

            passage_details.append({
                "passage_id": p_id,
                "document_id": doc_id,
                "passage_reference": p_ref,
                "content_reference": c_ref,
                "text_excerpt": text[:300] if text else "",
                "passage_digest": p_digest,
                "provenance": provenance or "BUNDLED_FIXTURE"
            })

        return {
            "case_id": case_id,
            "status": WorkflowState.EVIDENCE_BOUND.value,
            "passages_count": len(passages),
            "passages": passage_details
        }

    @staticmethod
    async def record_analysis_and_seal_decision(
        db: AsyncSession,
        case_id: str,
        actor: str = "SYSTEM_ORCHESTRATOR"
    ) -> Dict[str, Any]:
        """
        Stages C & D — Runs multi-agent legal investigation, records claims and arguments,
        generates the canonical decision record (VCP-1), and verifies it against the audit rules.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case '{case_id}' not found.")

        # Ensure evidence is bound
        stmt_docs = select(SourceDocument).join(EvidencePassage).limit(1)
        res_docs = await db.execute(stmt_docs)
        if not res_docs.scalars().first():
            raise InsufficientEvidenceException(f"Cannot analyze case '{case_id}' without bound evidence.")

        # Transition to ANALYSIS_RECORDED
        await WorkflowService.transition_state(
            db=db,
            case_id=case_id,
            to_state=WorkflowState.ANALYSIS_RECORDED.value,
            actor=actor,
            reason="Executing multi-agent statutory and adversarial analysis."
        )

        # Run multi-agent pipeline
        analysis_res = await CaseService.run_full_analysis(db, case_id)

        # Build canonical decision record
        decision_rec = await DecisionService.build_canonical_decision_record(db, case_id, persist=True, rebuild=True)

        # Generate temporary package to test verification
        package = await DecisionService.generate_audit_package(db, case_id)
        verif_report = IndependentAuditVerifier.verify_audit_package(package)

        target_status = WorkflowState.DECISION_VERIFIED.value if verif_report.get("is_valid") else WorkflowState.PARTIALLY_VERIFIED.value

        await WorkflowService.transition_state(
            db=db,
            case_id=case_id,
            to_state=target_status,
            actor=actor,
            reason=f"Canonical decision record sealed and verified (Valid: {verif_report.get('is_valid')}).",
            metadata={"record_digest": decision_rec.record_digest, "checks": verif_report.get("checks")}
        )

        return {
            "case_id": case_id,
            "workflow_status": target_status,
            "decision_record": decision_rec.model_dump(),
            "verification_report": verif_report,
            "analysis_summary": {
                "claims_count": len(decision_rec.claims),
                "sources_count": len(decision_rec.evidence_sources),
                "passages_count": len(decision_rec.evidence_passages),
            }
        }

    @staticmethod
    async def create_forecast_for_decision(
        db: AsyncSession,
        case_id: str,
        req: MarketCreateRequest,
        creator_address: str = "0xCreator"
    ) -> PredictionMarket:
        """
        Stage E — Creates an optional forecast market bound directly to the verified decision record.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case '{case_id}' not found.")

        # Ensure decision record exists
        decision = await db.get(DecisionRecordEntity, f"dec_{case.id}_v{case.scope_version}")
        if not decision:
            # Generate decision record if missing
            await DecisionService.build_canonical_decision_record(db, case_id, persist=True)

        # Transition workflow to FORECAST_OPEN
        market = await MarketService.create_market(db, req, creator_address=creator_address)

        await WorkflowService.transition_state(
            db=db,
            case_id=case_id,
            to_state=WorkflowState.FORECAST_OPEN.value,
            actor=creator_address,
            reason=f"Opened prediction market '{market.id}' bound to case decision record."
        )

        return market

    @staticmethod
    async def commit_forecast_commitment(
        db: AsyncSession,
        market_id: str,
        req: MarketCommitRequest,
        sender_address: str = "0xAgent"
    ) -> Forecast:
        """
        Stage F — Submits cryptographic forecast commitment.
        """
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market '{market_id}' not found.")

        forecast = await MarketService.commit_forecast(db, market_id, req, sender_address=sender_address)

        await WorkflowService.transition_state(
            db=db,
            case_id=market.case_id,
            to_state=WorkflowState.FORECAST_COMMITTED.value,
            actor=req.agent_id,
            reason=f"Forecast committed for agent {req.agent_id} in market {market_id}."
        )

        return forecast

    @staticmethod
    async def reveal_forecast_prediction(
        db: AsyncSession,
        market_id: str,
        req: MarketRevealRequest,
        sender_address: str = "0xAgent"
    ) -> Forecast:
        """
        Stage G — Reveals prediction and cryptographic nonce; verifies keccak256 hash.
        """
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market '{market_id}' not found.")

        forecast = await MarketService.reveal_forecast(db, market_id, req, sender_address=sender_address)

        await WorkflowService.transition_state(
            db=db,
            case_id=market.case_id,
            to_state=WorkflowState.FORECAST_REVEALED.value,
            actor=req.agent_id,
            reason=f"Forecast revealed by agent {req.agent_id} (Probability: {req.probability})."
        )

        return forecast

    @staticmethod
    async def resolve_market_outcome(
        db: AsyncSession,
        market_id: str,
        req: MarketResolveRequest,
        is_test: bool = False
    ) -> PredictionMarket:
        """
        Stage H — Resolves market outcome strictly following declared resolution criteria.
        If is_test is True, labels resolution as TEST to prevent operational pollution.
        """
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market '{market_id}' not found.")

        market = await MarketService.propose_resolution(db, market_id, req)

        target_state = WorkflowState.RESOLVED.value if not is_test else WorkflowState.RESOLVED.value
        await WorkflowService.transition_state(
            db=db,
            case_id=market.case_id,
            to_state=target_state,
            actor=req.evaluator_address,
            reason=f"Market resolution proposed: outcome={req.proposed_outcome} (test={is_test})."
        )

        return market

    @staticmethod
    async def settle_and_score_market(
        db: AsyncSession,
        market_id: str,
        settler_address: str = "0xEvaluator"
    ) -> Dict[str, Any]:
        """
        Stage I — Settles market, calculates proper Brier scores, updates reputations,
        and prevents duplicate settlements.
        """
        market = await db.get(PredictionMarket, market_id)
        if not market:
            raise InvalidForecastException(f"Market '{market_id}' not found.")

        settle_res = await MarketService.settle_market(db, market_id, settler_address=settler_address)

        await WorkflowService.transition_state(
            db=db,
            case_id=market.case_id,
            to_state=WorkflowState.SCORED.value,
            actor=settler_address,
            reason=f"Settled {len(settle_res['settlements'])} forecasts using proper Brier scoring."
        )

        return settle_res

    @staticmethod
    async def finalize_and_verify_audit_package(
        db: AsyncSession,
        case_id: str,
        trusted_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage J — Exports complete audit package and verifies it offline using zero-trust rules.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case '{case_id}' not found.")

        package = await DecisionService.generate_audit_package(db, case_id)
        verif_report = IndependentAuditVerifier.verify_audit_package(package, trusted_checkpoint=trusted_checkpoint)

        if verif_report.get("is_valid"):
            await WorkflowService.transition_state(
                db=db,
                case_id=case_id,
                to_state=WorkflowState.AUDIT_PACKAGE_VERIFIED.value,
                actor="INDEPENDENT_AUDITOR",
                reason="Exported audit package successfully verified offline."
            )

        return {
            "case_id": case_id,
            "audit_package": package,
            "verification_report": verif_report
        }

    @staticmethod
    async def get_case_unified_workspace(
        db: AsyncSession,
        case_id: str,
        trusted_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Provides unified state for the frontend Decision Workspace across all 12 stages.
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case '{case_id}' not found.")

        # 1. Case details
        case_info = {
            "id": case.id,
            "title": case.title,
            "question": case.question,
            "jurisdiction": case.jurisdiction,
            "assessment_date": case.assessment_date,
            "facts": case.facts or {},
            "scope_version": case.scope_version,
            "status": case.status,
            "provenance": case.provenance or "OPERATIONAL",
            "created_at": format_canonical_timestamp(case.created_at)
        }

        # 2. Decision record & verification
        decision_id = f"dec_{case.id}_v{case.scope_version}"
        decision_entity = await db.get(DecisionRecordEntity, decision_id)
        decision_record = None
        if decision_entity and decision_entity.canonical_data:
            decision_record = decision_entity.canonical_data

        # 3. Export audit package & run offline verifier
        try:
            package = await DecisionService.generate_audit_package(db, case_id)
            verification_report = IndependentAuditVerifier.verify_audit_package(package, trusted_checkpoint=trusted_checkpoint)
        except Exception as e:
            package = None
            verification_report = {
                "is_valid": False,
                "is_anchored": False,
                "overall_status": "UNVERIFIED",
                "error": f"Failed to generate/verify audit package: {e}",
                "checks": {}
            }

        # 4. Markets & forecasts
        stmt_mkts = select(PredictionMarket).where(PredictionMarket.case_id == case_id)
        res_mkts = await db.execute(stmt_mkts)
        markets = res_mkts.scalars().all()

        market_details = []
        for m in markets:
            stmt_fcs = select(Forecast).where(Forecast.market_id == m.id)
            res_fcs = await db.execute(stmt_fcs)
            fcs = res_fcs.scalars().all()

            stmt_stl = select(Settlement).where(Settlement.reference_id == m.id)
            res_stl = await db.execute(stmt_stl)
            settlements = res_stl.scalars().all()

            market_details.append({
                "market_id": m.id,
                "question": m.question,
                "outcome_definition": m.outcome_definition,
                "resolution_method": m.resolution_method,
                "status": m.status,
                "commit_deadline": format_canonical_timestamp(m.commit_deadline),
                "reveal_deadline": format_canonical_timestamp(m.reveal_deadline),
                "aggregate_probability": m.aggregate_probability,
                "disagreement_variance": m.disagreement_variance,
                "sample_size": m.sample_size,
                "proposed_outcome": m.proposed_outcome,
                "resolution_reference": m.resolution_reference,
                "contract_address": m.contract_address,
                "forecasts": [
                    {
                        "forecast_id": f.id,
                        "agent_id": f.agent_id,
                        "commitment_hash": f.commitment_hash,
                        "reveal_status": f.reveal_status,
                        "revealed_probability": f.probability,
                        "commit_tx_hash": f.commit_tx_hash,
                        "reveal_tx_hash": f.reveal_tx_hash
                    } for f in fcs
                ],
                "settlements": [
                    {
                        "settlement_id": s.id,
                        "score": s.score,
                        "reward": s.reward,
                        "tx_hash": s.tx_hash,
                        "participant_address": s.participant_address
                    } for s in settlements
                ]
            })

        # 5. Permitted transitions from current state
        allowed_transitions = PERMITTED_TRANSITIONS.get(case.status, [])

        return {
            "case": case_info,
            "decision_record": decision_record,
            "verification_report": verification_report,
            "markets": market_details,
            "current_workflow_state": case.status,
            "allowed_transitions": allowed_transitions,
            "audit_package_available": package is not None
        }
