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
            created_at=utcnow(),
            updated_at=utcnow()
        )
        db.add(case)
        await db.flush()

        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="CASE_CREATED",
            actor=creator_address,
            payload={
                "title": case.title,
                "jurisdiction": case.jurisdiction,
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
    async def get_all_cases(db: AsyncSession) -> List[Case]:
        stmt = select(Case).order_by(Case.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_case(db: AsyncSession, case_id: str, req: CaseUpdateRequest, actor_address: str = "0xUser") -> Case:
        case = await db.get(Case, case_id)
        if not case:
            return None

        # Material edits increment scope_version (FR-003)
        version_incremented = False
        if req.title and req.title != case.title:
            case.title = req.title
            version_incremented = True
        if req.question and req.question != case.question:
            case.question = req.question
            version_incremented = True
        if req.facts:
            case.facts = req.facts
            version_incremented = True

        if version_incremented:
            case.scope_version += 1
            case.status = "DRAFT"

        case.updated_at = utcnow()
        await db.flush()

        await AuditService.log_event(
            db=db,
            case_id=case.id,
            event_type="CASE_UPDATED",
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
        5. Evidence Verifier Agent for digest verification
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

        # Step 5: Evidence Verifier
        verifier_out = await AgentService.run_evidence_verifier(
            db,
            claims=researcher_out.claims + interpreter_out.claims
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

        # Retrieve full argument graph
        graph = await ArgumentService.get_argument_graph(db, case.id)

        return {
            "case_id": case.id,
            "scope_version": case.scope_version,
            "status": case.status,
            "agent_outputs": [
                researcher_out.model_dump(),
                interpreter_out.model_dump(),
                adversary_out.model_dump(),
                verifier_out.model_dump()
            ],
            "baseline_forecast": forecast_out,
            "argument_graph": graph,
            "ranked_uncertainties": coordinator_out["ranked_uncertainties"]
        }

    @staticmethod
    async def stream_full_analysis(db: AsyncSession, case_id: str):
        """
        Asynchronous generator yielding real-time SSE progress events for frontend Agent Laboratory.
        """
        case = await db.get(Case, case_id)
        if not case:
            yield f"event: error\ndata: {json.dumps({'error': f'Case {case_id} not found'})}\n\n"
            return

        yield f"event: progress\ndata: {json.dumps({'status': 'RETRIEVAL', 'message': 'Searching curated legal corpus...'})}\n\n"

        passages = await RetrievalService.retrieve_passages(
            db=db,
            query=f"{case.question} {' '.join(case.facts.get('data_categories', []))} {case.facts.get('processing_purpose', '')}",
            jurisdiction=case.jurisdiction,
            limit=5
        )
        yield f"event: retrieval_complete\ndata: {json.dumps({'passages_count': len(passages)})}\n\n"

        # Researcher
        yield f"event: agent_running\ndata: {json.dumps({'role': 'LEGAL_RESEARCHER', 'message': 'Extracting statutory propositions...'})}\n\n"
        researcher_out = await AgentService.run_legal_researcher(db, case, passages)
        yield f"event: agent_complete\ndata: {json.dumps({'role': 'LEGAL_RESEARCHER', 'output': researcher_out.model_dump()})}\n\n"

        # Interpreter
        yield f"event: agent_running\ndata: {json.dumps({'role': 'LEGAL_INTERPRETER', 'message': 'Evaluating deterministic rule checks...'})}\n\n"
        interpreter_out = await AgentService.run_legal_interpreter(db, case, researcher_out.claims, passages)
        yield f"event: agent_complete\ndata: {json.dumps({'role': 'LEGAL_INTERPRETER', 'output': interpreter_out.model_dump()})}\n\n"

        # Adversary
        yield f"event: agent_running\ndata: {json.dumps({'role': 'ADVERSARIAL_RESEARCHER', 'message': 'Searching exceptions and stress-testing claims...'})}\n\n"
        adversary_out = await AgentService.run_adversarial_researcher(db, case, interpreter_out.claims)
        yield f"event: agent_complete\ndata: {json.dumps({'role': 'ADVERSARIAL_RESEARCHER', 'output': adversary_out.model_dump()})}\n\n"

        # Verifier
        verifier_out = await AgentService.run_evidence_verifier(db, claims=researcher_out.claims + interpreter_out.claims)
        yield f"event: agent_complete\ndata: {json.dumps({'role': 'EVIDENCE_VERIFIER', 'output': verifier_out.model_dump()})}\n\n"

        # Forecaster
        forecast_out = await AgentService.run_quantitative_forecaster(db, case, interpreter_out.claims)
        yield f"event: agent_complete\ndata: {json.dumps({'role': 'QUANTITATIVE_FORECASTER', 'forecast': forecast_out})}\n\n"

        # Coordinator
        coordinator_out = await AgentService.run_coordinator(
            db=db,
            case=case,
            all_agent_outputs=[researcher_out, interpreter_out, adversary_out]
        )
        case.status = "COMPLETED"
        await db.commit()

        graph = await ArgumentService.get_argument_graph(db, case.id)
        yield f"event: analysis_complete\ndata: {json.dumps({'case_id': case.id, 'argument_graph': graph, 'ranked_uncertainties': coordinator_out['ranked_uncertainties']})}\n\n"
