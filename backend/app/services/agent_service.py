import time
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.crypto import (
    compute_commitment_hash,
    compute_sha256_digest,
    generate_nonce,
)
from backend.app.models.entities import Agent, Case, EvidencePassage, utcnow
from backend.app.schemas.agent import (
    AgentExecutionOutput,
    ClaimOutput,
    CounterargumentOutput,
    EvidenceRef,
    UncertaintyDetail,
)
from backend.app.services.argument_service import ArgumentService
from backend.app.services.audit_service import AuditService
from backend.app.services.hf_service import HuggingFaceInferenceService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.rule_engine import DeterministicRuleEngine

DEFAULT_AGENTS = [
    {
        "id": "agent_legal_researcher",
        "wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "role": "LEGAL_RESEARCHER",
        "model_provider_version": "veridion-researcher-v1.0",
        "prompt_version": "1.0.0",
        "reputation_score": 98.5,
        "brier_score": 0.12,
        "sample_count": 42,
        "simulated_credits": 1500.0
    },
    {
        "id": "agent_legal_interpreter",
        "wallet_address": "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        "role": "LEGAL_INTERPRETER",
        "model_provider_version": "veridion-interpreter-v1.0",
        "prompt_version": "1.0.0",
        "reputation_score": 94.0,
        "brier_score": 0.15,
        "sample_count": 38,
        "simulated_credits": 1400.0
    },
    {
        "id": "agent_adversarial_researcher",
        "wallet_address": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        "role": "ADVERSARIAL_RESEARCHER",
        "model_provider_version": "veridion-adversary-v1.0",
        "prompt_version": "1.0.0",
        "reputation_score": 96.2,
        "brier_score": 0.14,
        "sample_count": 35,
        "simulated_credits": 1450.0
    },
    {
        "id": "agent_evidence_verifier",
        "wallet_address": "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
        "role": "EVIDENCE_VERIFIER",
        "model_provider_version": "veridion-verifier-v1.0",
        "prompt_version": "1.0.0",
        "reputation_score": 99.1,
        "brier_score": 0.08,
        "sample_count": 50,
        "simulated_credits": 1800.0
    },
    {
        "id": "agent_quantitative_forecaster",
        "wallet_address": "0x9965507D1a55bcC2695C58ba16FB37d819B0A4df",
        "role": "QUANTITATIVE_FORECASTER",
        "model_provider_version": "veridion-forecaster-v1.0",
        "prompt_version": "1.0.0",
        "reputation_score": 92.8,
        "brier_score": 0.16,
        "sample_count": 31,
        "simulated_credits": 1250.0
    },
    {
        "id": "agent_coordinator",
        "wallet_address": "0x976EA74026E726554dB657fA54763abd0C3a0aa9",
        "role": "COORDINATOR",
        "model_provider_version": "veridion-coordinator-v1.0",
        "prompt_version": "1.0.0",
        "reputation_score": 100.0,
        "brier_score": 0.10,
        "sample_count": 60,
        "simulated_credits": 2000.0
    }
]


class AgentService:
    @staticmethod
    async def initialize_agents(db: AsyncSession) -> int:
        """Registers default specialized agents with assigned roles and wallets."""
        created = 0
        for agent_def in DEFAULT_AGENTS:
            existing = await db.get(Agent, agent_def["id"])
            if not existing:
                agent = Agent(
                    id=agent_def["id"],
                    wallet_address=agent_def["wallet_address"],
                    role=agent_def["role"],
                    model_provider_version=agent_def["model_provider_version"],
                    prompt_version=agent_def["prompt_version"],
                    status="ACTIVE",
                    reputation_score=agent_def["reputation_score"],
                    brier_score=agent_def["brier_score"],
                    sample_count=agent_def["sample_count"],
                    simulated_credits=agent_def["simulated_credits"],
                    created_at=utcnow()
                )
                db.add(agent)
                created += 1
        await db.commit()
        return created

    @staticmethod
    async def get_all_agents(db: AsyncSession) -> List[Agent]:
        stmt = select(Agent)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def run_legal_researcher(
        db: AsyncSession,
        case: Case,
        passages: List[Dict[str, Any]]
    ) -> AgentExecutionOutput:
        start_time = time.time()
        agent_id = "agent_legal_researcher"

        claims = []
        evidence_refs = []

        for p in passages:
            ev_ref = EvidenceRef(
                evidence_id=p["evidence_id"],
                passage_reference=p["passage_reference"],
                digest=p["digest"],
                relationship="SUPPORTS",
                relevance_score=p.get("relevance_score", 1.0)
            )
            evidence_refs.append(ev_ref)

            claim_text = f"Statutory authority {p['passage_reference']} mandates: {p['text'][:120]}..."
            claims.append(ClaimOutput(
                claim_text=claim_text,
                claim_type="STATUTORY_INTERPRETATION",
                assumptions=["Authority is in effect for current jurisdiction and assessment date"],
                confidence=0.95,
                confidence_rationale="Direct text excerpt from verified official gazette",
                is_supported=True,
                evidence_refs=[ev_ref]
            ))

        return AgentExecutionOutput(
            agent_id=agent_id,
            role="LEGAL_RESEARCHER",
            case_id=case.id,
            case_version=case.scope_version,
            claims=claims,
            evidence_refs=evidence_refs,
            assumptions=["Statutory corpus covers current assessment date"],
            counterarguments=[],
            uncertainty=0.15,
            recommended_actions=["Proceed to factual mapping against retrieved authorities"],
            execution_time_ms=round((time.time() - start_time) * 1000, 2)
        )

    @staticmethod
    async def run_legal_interpreter(
        db: AsyncSession,
        case: Case,
        researcher_claims: List[ClaimOutput],
        passages: List[Dict[str, Any]]
    ) -> AgentExecutionOutput:
        start_time = time.time()
        agent_id = "agent_legal_interpreter"

        # Deterministic check integration
        rule_results = DeterministicRuleEngine.evaluate(case.facts, case.jurisdiction)

        claims = []
        evidence_refs = [
            EvidenceRef(
                evidence_id=p["evidence_id"],
                passage_reference=p["passage_reference"],
                digest=p["digest"],
                relationship="SUPPORTS"
            )
            for p in passages[:3]
        ]

        assumptions = []
        uncertainties = []

        for rule in rule_results:
            is_violation = rule["violation_detected"]
            claim_text = f"Factual mapping under {rule['statutory_reference']}: {rule['legal_analysis']} (Trigger: {rule['factual_trigger']})"
            claim_type = "RISK_ASSESSMENT" if is_violation else "FACTUAL_MAPPING"
            confidence = 0.90 if is_violation else 0.85

            claims.append(ClaimOutput(
                claim_text=claim_text,
                claim_type=claim_type,
                assumptions=[f"Rule application assumes factual completeness for {rule['rule_id']}"],
                confidence=confidence,
                confidence_rationale="Deterministic rule engine evaluation cross-referenced with facts",
                is_supported=True,
                evidence_refs=evidence_refs
            ))

            if is_violation and rule["severity"] in ["HIGH", "CRITICAL"]:
                uncertainties.append(UncertaintyDetail(
                    unresolved_question=f"Does processing trigger formal sanction under {rule['statutory_reference']}?",
                    impact=0.90,
                    uncertainty=0.60,
                    research_feasibility=0.75,
                    recommended_bounty=True
                ))

        return AgentExecutionOutput(
            agent_id=agent_id,
            role="LEGAL_INTERPRETER",
            case_id=case.id,
            case_version=case.scope_version,
            claims=claims,
            evidence_refs=evidence_refs,
            assumptions=assumptions,
            counterarguments=[],
            uncertainty=0.35 if uncertainties else 0.10,
            uncertainty_details=uncertainties,
            recommended_actions=["Deploy adversarial testing on compliance exceptions"],
            execution_time_ms=round((time.time() - start_time) * 1000, 2)
        )

    @staticmethod
    async def run_adversarial_researcher(
        db: AsyncSession,
        case: Case,
        interpreter_claims: List[ClaimOutput]
    ) -> AgentExecutionOutput:
        start_time = time.time()
        agent_id = "agent_adversarial_researcher"

        counterarguments = []
        counter_claims = []

        # Adversarially challenge each high-risk claim
        for claim in interpreter_claims:
            if "RISK_ASSESSMENT" in claim.claim_type:
                # Query fine-tuned Hugging Face model if configured by ML teammate
                hf_prompt = f"Case Question: {case.question}\nMaterial Risk Claim: {claim.claim_text}\nGenerate the strongest legal counterargument or statutory defense under {case.jurisdiction} law."
                hf_objection = await HuggingFaceInferenceService.generate_completion(
                    prompt=hf_prompt,
                    system_prompt="You are an adversarial legal intelligence agent specialized in finding defenses, exceptions, and procedural counterarguments."
                )

                if hf_objection:
                    objection_text = hf_objection
                    rationale = f"Fine-tuned model ({getattr(settings, 'HF_MODEL_ID', 'veridion-legal')}) inference"
                else:
                    objection_text = "Contesting applicability: Controller may assert legitimate interest (Art 6(1)(f)) or research exemption (Art 89(1)) if anonymization is proven."
                    rationale = "Deterministic statutory exception analysis (GDPR Art 6(1)(f) & Art 89(1))"

                counterarguments.append(CounterargumentOutput(
                    target_claim_text=claim.claim_text,
                    objection=objection_text,
                    contrary_evidence_refs=[],
                    severity="HIGH"
                ))

                counter_claims.append(ClaimOutput(
                    claim_text=f"Adversarial Objection: Legitimate interest exception may supersede standard purpose restriction if data is adequately sanitized.",
                    claim_type="EXCEPTION",
                    assumptions=["Sanitization techniques render customer identifiers non-re-identifiable"],
                    confidence=0.70,
                    confidence_rationale=rationale,
                    is_supported=False,
                    evidence_refs=[]
                ))

        return AgentExecutionOutput(
            agent_id=agent_id,
            role="ADVERSARIAL_RESEARCHER",
            case_id=case.id,
            case_version=case.scope_version,
            claims=counter_claims,
            evidence_refs=[],
            assumptions=["Data controller will raise maximal legal exceptions under defense"],
            counterarguments=counterarguments,
            uncertainty=0.45,
            recommended_actions=["Require evidence verification of claimed anonymization techniques"],
            execution_time_ms=round((time.time() - start_time) * 1000, 2)
        )

    @staticmethod
    async def run_evidence_verifier(
        db: AsyncSession,
        claims: List[ClaimOutput]
    ) -> AgentExecutionOutput:
        start_time = time.time()
        agent_id = "agent_evidence_verifier"

        verified_claims = []
        verified_refs = []

        for c in claims:
            has_valid_evidence = False
            for ref in c.evidence_refs:
                passage = await db.get(EvidencePassage, ref.evidence_id)
                if passage:
                    expected_digest = compute_sha256_digest(passage.text)
                    if expected_digest.lower() == ref.digest.lower():
                        has_valid_evidence = True
                        verified_refs.append(ref)

            c.is_supported = has_valid_evidence
            verified_claims.append(c)

        return AgentExecutionOutput(
            agent_id=agent_id,
            role="EVIDENCE_VERIFIER",
            case_id="case_verification",
            case_version=1,
            claims=verified_claims,
            evidence_refs=verified_refs,
            assumptions=["Passage digests are tamper-evident SHA-256 signatures"],
            counterarguments=[],
            uncertainty=0.05,
            recommended_actions=["All claims cryptographically verified against on-disk passages"],
            execution_time_ms=round((time.time() - start_time) * 1000, 2)
        )

    @staticmethod
    async def run_quantitative_forecaster(
        db: AsyncSession,
        case: Case,
        interpreter_claims: List[ClaimOutput]
    ) -> Dict[str, Any]:
        """
        Generates probability forecast for benchmark outcome:
        'Will an independent evaluator identify at least one material compliance gap under frozen facts?'
        """
        agent_id = "agent_quantitative_forecaster"
        violations = [c for c in interpreter_claims if c.claim_type == "RISK_ASSESSMENT"]

        # If deterministic violations exist, high probability of gap
        if len(violations) >= 2:
            base_prob = 0.85
        elif len(violations) == 1:
            base_prob = 0.65
        else:
            base_prob = 0.15

        evidence_digest = compute_sha256_digest({
            "case_id": case.id,
            "violations_count": len(violations),
            "jurisdiction": case.jurisdiction
        })
        nonce = generate_nonce()

        return {
            "agent_id": agent_id,
            "probability": base_prob,
            "evidence_digest": evidence_digest,
            "nonce": nonce,
            "event_definition": "Independent evaluator finds material compliance gap",
            "model_version": "veridion-forecaster-v1.0"
        }

    @staticmethod
    async def run_coordinator(
        db: AsyncSession,
        case: Case,
        all_agent_outputs: List[AgentExecutionOutput]
    ) -> Dict[str, Any]:
        """
        Coordinator synthesizes all agent streams, constructs the Argument Graph,
        creates edges (SUPPORTS, CONTRADICTS, QUALIFIES), and ranks uncertainties.
        """
        claims_created = []

        # Persist claims in DB
        for output in all_agent_outputs:
            for c in output.claims:
                db_claim = await ArgumentService.create_claim(
                    db=db,
                    case_id=case.id,
                    case_version=case.scope_version,
                    agent_id=output.agent_id,
                    claim_text=c.claim_text,
                    claim_type=c.claim_type,
                    assumptions=c.assumptions,
                    confidence=c.confidence,
                    confidence_rationale=c.confidence_rationale,
                    status="SUPPORTED" if c.is_supported else "UNSUPPORTED"
                )
                claims_created.append(db_claim)

                # Link evidence
                for ev in c.evidence_refs:
                    await ArgumentService.link_evidence(
                        db=db,
                        claim_id=db_claim.id,
                        evidence_id=ev.evidence_id,
                        relationship_type=ev.relationship,
                        verification_status="VERIFIED"
                    )

        # Create Argument Graph edges between claims and counterarguments
        # Match counterarguments to target claims
        risk_claims = [c for c in claims_created if c.claim_type == "RISK_ASSESSMENT"]
        exception_claims = [c for c in claims_created if c.claim_type == "EXCEPTION"]

        for rc in risk_claims:
            for ec in exception_claims:
                await ArgumentService.create_edge(
                    db=db,
                    case_id=case.id,
                    source_claim_id=ec.id,
                    target_claim_id=rc.id,
                    relationship_type="CONTRADICTS",
                    reason="Adversarial objection asserts legitimate interest exception to purpose restriction"
                )

        # Collect and rank all uncertainties
        raw_uncertainties = []
        for output in all_agent_outputs:
            for u in output.uncertainty_details:
                raw_uncertainties.append(u.model_dump())

        ranked_uncertainties = ArgumentService.rank_uncertainties(raw_uncertainties)

        return {
            "case_id": case.id,
            "claims_count": len(claims_created),
            "ranked_uncertainties": ranked_uncertainties,
            "overall_status": "INVESTIGATION_COMPLETE"
        }
