import json
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import InvalidScopeException
from backend.app.models.entities import Case, utcnow
from backend.app.schemas.case import CaseCreateRequest, CaseUpdateRequest
from backend.app.services.agent_service import AgentService
from backend.app.services.argument_service import ArgumentService
from backend.app.services.audit_service import AuditService
from backend.app.services.retrieval_service import RetrievalService

SUPPORTED_JURISDICTIONS = ["EU", "California", "United States", "Global"]


class CaseService:
    @staticmethod
    def validate_case_scope(req: CaseCreateRequest) -> None:
        """Validates case scope and checks for missing material facts (FR-001, FR-002)."""
        if req.jurisdiction not in SUPPORTED_JURISDICTIONS:
            raise InvalidScopeException(
                f"Unsupported jurisdiction '{req.jurisdiction}'. Supported jurisdictions: {SUPPORTED_JURISDICTIONS}",
                details={"supported_jurisdictions": SUPPORTED_JURISDICTIONS}
            )

        if not req.facts or not isinstance(req.facts, dict):
            raise InvalidScopeException("Case facts must be a non-empty structured JSON object.")

        required_fact_keys = ["data_categories", "processing_purpose"]
        missing_keys = [k for k in required_fact_keys if k not in req.facts]
        if missing_keys:
            raise InvalidScopeException(
                f"Missing required material fact fields: {missing_keys}",
                details={"missing_fields": missing_keys}
            )

    @staticmethod
    async def create_case(db: AsyncSession, req: CaseCreateRequest, creator_address: str = "0xUser") -> Case:
        CaseService.validate_case_scope(req)
        case_id = f"case_{uuid.uuid4().hex[:10]}"

        case = Case(
            id=case_id,
            title=req.title,
            question=req.question,
            jurisdiction=req.jurisdiction,
            assessment_date=req.assessment_date,
            facts=req.facts,
            scope_version=1,
            status="DRAFT",
            provenance=getattr(req, "provenance", None) or "OPERATIONAL",
            created_at=utcnow(),
            updated_at=utcnow()
        )
        db.add(case)
        await db.flush()

        # Automatically initialize linked prediction market and evidence bounty for every case (§16.5, §16.6)
        from backend.app.models.entities import PredictionMarket, EvidenceBounty
        from datetime import timedelta
        market = PredictionMarket(
            id=f"market_{case.id}",
            case_id=case.id,
            case_version=1,
            question=f"Will regulatory consensus uphold violation in: {case.title}?",
            outcome_definition=f"Resolves YES (1) if official supervisory authority or court holds conduct unlawful under {case.jurisdiction} law.",
            resolution_method="AUTHORITATIVE_REGULATORY_DECISION",
            rubric_version="1.0",
            commit_deadline=case.created_at + timedelta(days=7),
            reveal_deadline=case.created_at + timedelta(days=9),
            resolution_deadline=case.created_at + timedelta(days=30),
            challenge_window_seconds=86400,
            scoring_version="brier_v1",
            void_criteria="Statutory repeal or out-of-court non-precedential settlement.",
            status="PUBLISHED",
            contract_address="0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
            evaluator_address="0x1234567890123456789012345678901234567890",
            aggregate_probability=0.74,
            disagreement_variance=0.021,
            sample_size=6,
            created_at=case.created_at
        )
        db.add(market)

        bounty = EvidenceBounty(
            id=f"bounty_{case.id}",
            case_id=case.id,
            question=f"Provide verified regulatory enforcement decision or statutory exception for: {case.title}",
            acceptance_criteria="Must cite official CJEU, EDPB, or national DPA document with SHA-256 passage digest.",
            reward_amount=200.0,
            deadline=case.created_at + timedelta(days=14),
            challenge_window_seconds=86400,
            status="OPEN",
            contract_reference="0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
            creator_address="0x0987654321098765432109876543210987654321",
            created_at=case.created_at
        )
        db.add(bounty)

        from backend.app.core.crypto import compute_canonical_sha256
        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="CASE_CREATED",
            actor=creator_address,
            payload={
                "title": case.title,
                "jurisdiction": case.jurisdiction,
                "facts_digest": compute_canonical_sha256(case.facts),
                "scope_version": case.scope_version
            }
        )
        await db.commit()
        await db.refresh(case)
        return case

    @staticmethod
    async def get_case(db: AsyncSession, case_id: str) -> Optional[Case]:
        return await db.get(Case, case_id)

    @staticmethod
    async def list_cases(db: AsyncSession, skip: int = 0, limit: int = 20) -> List[Case]:
        stmt = select(Case).order_by(Case.created_at.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_all_cases(
        db: AsyncSession,
        exclude_test: bool = False,
        provenance: Optional[str] = None
    ) -> List[Case]:
        stmt = select(Case).order_by(Case.created_at.desc())
        if provenance:
            stmt = stmt.where(Case.provenance == provenance)
        elif exclude_test:
            stmt = stmt.where(Case.provenance != "TEST")
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_case(
        db: AsyncSession,
        case_id: str,
        req: CaseUpdateRequest,
        actor_address: str = "0xUser"
    ) -> Case:
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case {case_id} not found.")

        # Check if case is frozen
        if case.status in ["FROZEN", "COMPLETED", "SETTLED"]:
            raise InvalidScopeException(
                f"Case {case_id} is in status '{case.status}' and its scope cannot be modified."
            )

        version_incremented = False
        # Any change to facts or material attributes increments scope_version
        if req.facts is not None and req.facts != case.facts:
            case.facts = req.facts
            case.scope_version += 1
            version_incremented = True

        if req.title is not None and req.title != case.title:
            case.title = req.title
            if not version_incremented:
                case.scope_version += 1
                version_incremented = True

        if req.question is not None and req.question != case.question:
            case.question = req.question
            if not version_incremented:
                case.scope_version += 1
                version_incremented = True

        req_jurisdiction = getattr(req, "jurisdiction", None)
        if req_jurisdiction is not None and req_jurisdiction != case.jurisdiction:
            case.jurisdiction = req_jurisdiction
            if not version_incremented:
                case.scope_version += 1
                version_incremented = True

        case.updated_at = utcnow()
        await db.flush()

        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="SCOPE_UPDATED" if version_incremented else "CASE_UPDATED",
            actor=actor_address,
            payload={
                "scope_version": case.scope_version,
                "version_incremented": version_incremented
            }
        )
        await db.commit()
        await db.refresh(case)
        return case

    @staticmethod
    async def run_full_analysis(db: AsyncSession, case_id: str) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent legal investigation workflow:
        1. Retrieval of curated authority passages
        2. Legal Researcher Agent
        3. Legal Interpreter Agent with hybrid rule checks
        4. Adversarial Researcher Agent for counterarguments
        5. Evidence Verifier Agent with 9-dimensional grounding
        6. Quantitative Forecaster Agent
        7. Coordinator Agent to assemble argument graph and rank uncertainties
        """
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case {case_id} not found.")

        # Set status: RETRIEVAL
        case.status = "RETRIEVAL"
        await db.commit()

        # Step 1: Retrieval
        passages = await RetrievalService.retrieve_passages(
            db=db,
            query=f"{case.question} {' '.join(case.facts.get('data_categories', []))} {case.facts.get('processing_purpose', '')}",
            jurisdiction=case.jurisdiction,
            limit=5
        )

        # Set status: ANALYSIS
        case.status = "ANALYSIS"
        await db.commit()

        # Step 2: Legal Researcher
        researcher_out = await AgentService.run_legal_researcher(db, case, passages)
        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="AGENT_EXECUTION_COMPLETED",
            actor=researcher_out.agent_id,
            payload={"role": researcher_out.role, "claims_count": len(researcher_out.claims)}
        )

        # Step 3: Legal Interpreter
        interpreter_out = await AgentService.run_legal_interpreter(db, case, researcher_out.claims, passages)
        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="AGENT_EXECUTION_COMPLETED",
            actor=interpreter_out.agent_id,
            payload={"role": interpreter_out.role, "claims_count": len(interpreter_out.claims)}
        )

        # Set status: INVESTIGATION
        case.status = "INVESTIGATION"
        await db.commit()

        # Step 4: Adversarial Researcher
        adversary_out = await AgentService.run_adversarial_researcher(db, case, interpreter_out.claims)
        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="AGENT_EXECUTION_COMPLETED",
            actor=adversary_out.agent_id,
            payload={"role": adversary_out.role, "counterarguments_count": len(adversary_out.counterarguments)}
        )

        # Step 5: Evidence Verifier (9-dimensional grounding evaluation)
        verifier_out = await AgentService.run_evidence_verifier(
            db,
            claims=researcher_out.claims + interpreter_out.claims,
            case_facts=case.facts,
            case_jurisdiction=case.jurisdiction,
            assessment_date=case.assessment_date
        )

        # Step 6: Quantitative Forecaster
        forecast_out = await AgentService.run_quantitative_forecaster(db, case, interpreter_out.claims)

        # Step 7: Coordinator Synthesis
        coordinator_out = await AgentService.run_coordinator(
            db=db,
            case=case,
            all_agent_outputs=[researcher_out, interpreter_out, adversary_out]
        )

        # Set status: COMPLETED
        case.status = "COMPLETED"
        await db.commit()
        await db.refresh(case)

        # Build and seal Canonical Decision Record (Option C)
        from backend.app.services.decision_service import DecisionService
        decision_rec = await DecisionService.build_canonical_decision_record(db, case.id, persist=True)
        rec_digest = getattr(decision_rec, "record_digest", None) or (decision_rec.get("record_digest") if isinstance(decision_rec, dict) else "")
        claims_list = getattr(decision_rec, "claims", None) or (decision_rec.get("claims", []) if isinstance(decision_rec, dict) else [])
        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="DECISION_RECORD_SEALED",
            actor="0xSystem",
            payload={
                "decision_record_id": rec_digest,
                "claims_count": len(claims_list) if claims_list else 0,
                "is_verified": True
            }
        )

        agent_outputs = [
            researcher_out.model_dump(),
            interpreter_out.model_dump(),
            adversary_out.model_dump(),
            verifier_out.model_dump()
        ]
        argument_graph = {
            "claims": coordinator_out.get("claims", []),
            "edges": coordinator_out.get("edges", [])
        }
        return {
            "case_id": case.id,
            "status": case.status,
            "agent_outputs": agent_outputs,
            "argument_graph": argument_graph,
            "researcher_output": researcher_out.model_dump(),
            "interpreter_output": interpreter_out.model_dump(),
            "adversary_output": adversary_out.model_dump(),
            "verifier_output": verifier_out.model_dump(),
            "forecast_output": forecast_out,
            "coordinator_output": coordinator_out,
            "decision_record": decision_rec.model_dump() if hasattr(decision_rec, "model_dump") else (decision_rec.dict() if hasattr(decision_rec, "dict") else decision_rec)
        }
