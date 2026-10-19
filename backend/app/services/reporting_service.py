from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.errors import InvalidScopeException
from backend.app.models.entities import (
    AuditEvent,
    Case,
    Claim,
    ClaimEvidenceLink,
    EvidenceBounty,
    EvidencePassage,
    PredictionMarket,
    SourceDocument,
    utcnow,
)
from backend.app.schemas.report import (
    FinalCaseReport,
    ReportSection1ExecutiveSummary,
    ReportSection2FactsAndAssumptions,
    ReportSection3SourcesAndDates,
    ReportSection4PrincipalClaims,
    ReportSection5CounterargumentsAndConflicts,
    ReportSection6RiskFindings,
    ReportSection7Forecasts,
    ReportSection8BountiesAndUncertainties,
    ReportSection9Recommendations,
    ReportSection10AuditTrail,
)
from backend.app.services.argument_service import ArgumentService
from backend.app.services.rule_engine import DeterministicRuleEngine


class ReportingService:
    @staticmethod
    async def generate_final_report(db: AsyncSession, case_id: str) -> FinalCaseReport:
        case = await db.get(Case, case_id)
        if not case:
            raise InvalidScopeException(f"Case {case_id} not found.")

        # Section 1: Executive Summary
        rule_evals = DeterministicRuleEngine.evaluate(case.facts, case.jurisdiction)
        violations = [r for r in rule_evals if r["violation_detected"]]

        overall_risk = "LOW"
        if any(v["severity"] == "CRITICAL" for v in violations):
            overall_risk = "CRITICAL"
        elif any(v["severity"] == "HIGH" for v in violations):
            overall_risk = "HIGH"
        elif violations:
            overall_risk = "MEDIUM"

        summary_text = (
            f"VERIDION Legal Intelligence protocol completed multi-agent investigation for case '{case.title}'. "
            f"Analyzed against {case.jurisdiction} regulatory framework as of {case.assessment_date}. "
            f"Detected {len(violations)} material statutory compliance issues under deterministic hybrid verification. "
            f"Overall compliance risk is assessed as {overall_risk}."
        )

        sec1 = ReportSection1ExecutiveSummary(
            case_id=case.id,
            case_version=case.scope_version,
            title=case.title,
            jurisdiction=case.jurisdiction,
            question=case.question,
            assessment_date=case.assessment_date,
            overall_risk_level=overall_risk,
            executive_summary_text=summary_text
        )

        # Section 2: Facts and Assumptions
        sec2 = ReportSection2FactsAndAssumptions(
            facts=case.facts,
            implicit_assumptions=[
                "Assessment assumes complete disclosure of all processing pipelines",
                "Assumes technical operations correspond to stated architecture parameters"
            ],
            missing_facts_identified=[
                "Third-party sub-processor data sharing agreements",
                "Encryption-at-rest certificate management"
            ]
        )

        # Section 3: Relevant Sources & Effective Dates
        stmt_docs = select(SourceDocument).where(SourceDocument.jurisdiction == case.jurisdiction)
        docs_res = await db.execute(stmt_docs)
        docs = docs_res.scalars().all()
        sec3 = ReportSection3SourcesAndDates(
            sources=[
                {
                    "id": d.id,
                    "title": d.title,
                    "authority": d.authority,
                    "jurisdiction": d.jurisdiction,
                    "effective_date": d.effective_date,
                    "digest": d.digest,
                    "url": d.url
                }
                for d in docs
            ]
        )

        # Section 4: Principal Claims & Evidence
        graph = await ArgumentService.get_argument_graph(db, case.id)
        sec4 = ReportSection4PrincipalClaims(
            claims=graph["claims"]
        )

        # Section 5: Counterarguments & Conflicts
        sec5 = ReportSection5CounterargumentsAndConflicts(
            counterarguments=[
                {
                    "source": e["source_claim_id"],
                    "target": e["target_claim_id"],
                    "objection": e["reason"]
                }
                for e in graph["edges"] if e["relationship_type"] == "CONTRADICTS"
            ],
            detected_conflicts=graph["conflicts"]
        )

        # Section 6: Risk Findings & Rule Engine Checks
        sec6 = ReportSection6RiskFindings(
            findings=rule_evals,
            confidence_limitations=[
                "Model-generated arguments are probabilistic forecasts, not judicial rulings",
                "Statutory interpretations are subject to judicial and administrative agency discretion"
            ]
        )

        # Section 7: Prediction Market Forecasts
        stmt_markets = select(PredictionMarket).where(PredictionMarket.case_id == case.id)
        mkts_res = await db.execute(stmt_markets)
        markets = mkts_res.scalars().all()
        sec7 = ReportSection7Forecasts(
            markets=[
                {
                    "market_id": m.id,
                    "question": m.question,
                    "aggregate_probability": m.aggregate_probability,
                    "disagreement_variance": m.disagreement_variance,
                    "sample_size": m.sample_size,
                    "status": m.status,
                    "proposed_outcome": m.proposed_outcome
                }
                for m in markets
            ]
        )

        # Section 8: Bounties and Uncertainties
        stmt_bounties = select(EvidenceBounty).where(EvidenceBounty.case_id == case.id)
        bntys_res = await db.execute(stmt_bounties)
        bounties = bntys_res.scalars().all()

        sec8 = ReportSection8BountiesAndUncertainties(
            unresolved_questions=[
                {
                    "question": v["legal_analysis"],
                    "rule": v["rule_id"],
                    "statute": v["statutory_reference"],
                    "severity": v["severity"]
                }
                for v in violations
            ],
            bounties=[
                {
                    "bounty_id": b.id,
                    "question": b.question,
                    "reward": b.reward_amount,
                    "status": b.status,
                    "winner": b.winning_submission_id
                }
                for b in bounties
            ]
        )

        # Section 9: Recommendations & Escalation
        recommendations = [v["remedial_action"] for v in violations if v.get("remedial_action") != "None"]
        if not recommendations:
            recommendations = ["Maintain continuous automated audit telemetry."]

        sec9 = ReportSection9Recommendations(
            recommended_actions=recommendations
        )

        # Section 10: Audit Trail & Transactions
        stmt_audit = (
            select(AuditEvent)
            .where(AuditEvent.case_id == case.id)
            .order_by(AuditEvent.timestamp.desc())
            .limit(20)
        )
        audit_res = await db.execute(stmt_audit)
        events = audit_res.scalars().all()

        sec10 = ReportSection10AuditTrail(
            audit_events_count=len(events),
            recent_transactions=[
                {
                    "event_type": ev.event_type,
                    "actor": ev.actor,
                    "tx_hash": ev.tx_hash,
                    "payload_digest": ev.payload_digest,
                    "timestamp": ev.timestamp.isoformat()
                }
                for ev in events
            ]
        )

        return FinalCaseReport(
            case_id=case.id,
            case_version=case.scope_version,
            generated_at=utcnow(),
            section1_executive_summary=sec1,
            section2_facts_and_assumptions=sec2,
            section3_sources_and_dates=sec3,
            section4_principal_claims=sec4,
            section5_counterarguments_and_conflicts=sec5,
            section6_risk_findings=sec6,
            section7_forecasts=sec7,
            section8_bounties_and_uncertainties=sec8,
            section9_recommendations=sec9,
            section10_audit_trail=sec10
        )

    @staticmethod
    def export_markdown(report: FinalCaseReport) -> str:
        """Assembles the complete 10-section report into formatted Markdown (PRD 16.8)."""
        sec1 = report.section1_executive_summary
        sec2 = report.section2_facts_and_assumptions
        sec3 = report.section3_sources_and_dates
        sec4 = report.section4_principal_claims
        sec5 = report.section5_counterarguments_and_conflicts
        sec6 = report.section6_risk_findings
        sec7 = report.section7_forecasts
        sec8 = report.section8_bounties_and_uncertainties
        sec9 = report.section9_recommendations
        sec10 = report.section10_audit_trail

        md = f"""# VERIDION Protocol — Final Legal Assessment Report
**Case ID**: `{report.case_id}` (Version {report.case_version})  
**Generated At**: {report.generated_at.isoformat()}  
**Jurisdiction**: {sec1.jurisdiction} | **Overall Risk**: **{sec1.overall_risk_level}**

---

## 1. Executive Summary and Scope
- **Question**: {sec1.question}
- **Assessment Date**: {sec1.assessment_date}
- **Summary**: {sec1.executive_summary_text}

## 2. Facts and Assumptions
- **Supplied Facts**: {sec2.facts}
- **Implicit Assumptions**: {', '.join(sec2.implicit_assumptions)}
- **Missing Facts Identified**: {', '.join(sec2.missing_facts_identified)}

## 3. Relevant Sources and Effective Dates
| Authority | Document Title | Effective Date | SHA256 Digest |
|---|---|---|---|
"""
        for s in sec3.sources:
            md += f"| {s.get('authority')} | [{s.get('title')}]({s.get('url')}) | {s.get('effective_date')} | `{s.get('digest')[:18]}...` |\n"

        md += "\n## 4. Principal Claims and Evidence\n"
        for c in sec4.claims:
            md += f"- **[{c.get('claim_type')}]** {c.get('claim_text')} (Confidence: {c.get('confidence')})\n"

        md += "\n## 5. Counterarguments and Conflicts\n"
        for ca in sec5.counterarguments:
            md += f"- **Objection against `{ca.get('target')}`**: {ca.get('objection')}\n"

        md += "\n## 6. Risk Findings and Limitations\n"
        for f in sec6.findings:
            status_badge = "❌ VIOLATION" if f.get("violation_detected") else "✅ PASS"
            md += f"- **{f.get('rule_name')}** ({f.get('statutory_reference')}): {status_badge} - {f.get('legal_analysis')}\n"

        md += "\n## 7. Forecast Definitions and Probabilities\n"
        for m in sec7.markets:
            md += f"- **Market `{m.get('market_id')}`**: Aggregate Probability: **{m.get('aggregate_probability') * 100:.1f}%** (Variance: {m.get('disagreement_variance')}, N={m.get('sample_size')})\n"

        md += "\n## 8. Unresolved Uncertainties and Bounty Outcomes\n"
        for u in sec8.unresolved_questions:
            md += f"- Uncertainty: {u.get('question')} (Severity: {u.get('severity')})\n"

        md += "\n## 9. Recommended Next Steps and Human Review\n"
        for r in sec9.recommended_actions:
            md += f"1. {r}\n"
        md += f"\n> [!IMPORTANT]\n> {sec9.human_review_notice}\n"

        md += f"\n## 10. Audit References and Transaction Hashes\nTotal recorded audit events: {sec10.audit_events_count}\n"
        for tx in sec10.recent_transactions:
            md += f"- `{tx.get('event_type')}` by `{tx.get('actor')}` | TX: `{tx.get('tx_hash')}`\n"

        return md
