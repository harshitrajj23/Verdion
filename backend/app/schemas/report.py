from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportSection1ExecutiveSummary(BaseModel):
    case_id: str
    case_version: int
    title: str
    jurisdiction: str
    question: str
    assessment_date: str
    overall_risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    executive_summary_text: str


class ReportSection2FactsAndAssumptions(BaseModel):
    facts: Dict[str, Any]
    implicit_assumptions: List[str]
    missing_facts_identified: List[str]


class ReportSection3SourcesAndDates(BaseModel):
    sources: List[Dict[str, Any]]  # id, title, authority, effective_date, digest, url


class ReportSection4PrincipalClaims(BaseModel):
    claims: List[Dict[str, Any]]  # claim_text, claim_type, agent_role, status, evidence_refs


class ReportSection5CounterargumentsAndConflicts(BaseModel):
    counterarguments: List[Dict[str, Any]]
    detected_conflicts: List[Dict[str, Any]]


class ReportSection6RiskFindings(BaseModel):
    findings: List[Dict[str, Any]]  # rule_id, status, violation, severity, rule_text
    confidence_limitations: List[str]


class ReportSection7Forecasts(BaseModel):
    markets: List[Dict[str, Any]]  # market_id, question, aggregate_probability, disagreement_variance, sample_size, status


class ReportSection8BountiesAndUncertainties(BaseModel):
    unresolved_questions: List[Dict[str, Any]]  # question, impact, uncertainty, priority
    bounties: List[Dict[str, Any]]  # bounty_id, status, reward, winner


class ReportSection9Recommendations(BaseModel):
    recommended_actions: List[str]
    human_review_notice: str = Field(
        default="MANDATORY NOTICE: VERIDION provides automated decision-support protocol telemetry. It does not replace qualified legal counsel and does not constitute formal legal advice."
    )


class ReportSection10AuditTrail(BaseModel):
    audit_events_count: int
    recent_transactions: List[Dict[str, Any]]  # event_type, tx_hash, digest, timestamp


class FinalCaseReport(BaseModel):
    case_id: str
    case_version: int
    generated_at: datetime
    section1_executive_summary: ReportSection1ExecutiveSummary
    section2_facts_and_assumptions: ReportSection2FactsAndAssumptions
    section3_sources_and_dates: ReportSection3SourcesAndDates
    section4_principal_claims: ReportSection4PrincipalClaims
    section5_counterarguments_and_conflicts: ReportSection5CounterargumentsAndConflicts
    section6_risk_findings: ReportSection6RiskFindings
    section7_forecasts: ReportSection7Forecasts
    section8_bounties_and_uncertainties: ReportSection8BountiesAndUncertainties
    section9_recommendations: ReportSection9Recommendations
    section10_audit_trail: ReportSection10AuditTrail
