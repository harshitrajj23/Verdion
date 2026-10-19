/**
 * VERIDION Protocol - TypeScript API Types for Frontend Developer
 * Copy or import this file directly into your Next.js project (e.g. `src/types/veridion.ts`).
 */

export type CaseStatus = 
  | 'DRAFT' 
  | 'RETRIEVAL' 
  | 'ANALYSIS' 
  | 'INVESTIGATION' 
  | 'REVIEW' 
  | 'COMPLETED' 
  | 'FAILED';

export interface Case {
  id: string;
  title: string;
  question: string;
  jurisdiction: string;
  assessment_date: string;
  facts: Record<string, any>;
  scope_version: number;
  status: CaseStatus;
  created_at: string;
  updated_at: string;
}

export interface CaseCreateRequest {
  title: string;
  question: string;
  jurisdiction: string;
  assessment_date: string;
  facts: {
    data_categories: string[];
    processing_purpose: string;
    user_notice_provided?: boolean;
    user_consent_obtained?: boolean;
    retention_policy?: string;
    deletion_mechanism?: string;
    secondary_ai_training?: boolean;
    human_in_the_loop?: boolean;
    solely_automated_decision?: boolean;
    [key: string]: any;
  };
  document_references?: string[];
}

export interface EvidenceRef {
  evidence_id: string;
  passage_reference: string;
  digest: string;
  relationship: 'SUPPORTS' | 'REFUTES' | 'QUALIFIES';
  relevance_score: number;
}

export interface Claim {
  id: string;
  agent_id: string;
  claim_text: string;
  claim_type: 'STATUTORY_INTERPRETATION' | 'FACTUAL_MAPPING' | 'RISK_ASSESSMENT' | 'EXCEPTION';
  assumptions: string[];
  confidence: number;
  status: 'SUPPORTED' | 'UNSUPPORTED' | 'CONTESTED';
  timestamp: string;
}

export interface ArgumentEdge {
  id: string;
  source_claim_id: string;
  target_claim_id: string;
  relationship_type: 'SUPPORTS' | 'CONTRADICTS' | 'QUALIFIES' | 'DEPENDS_ON' | 'SUPERSEDES';
  reason: string;
  timestamp: string;
}

export interface ArgumentGraph {
  case_id: string;
  claims: Claim[];
  evidence_links: {
    id: string;
    claim_id: string;
    evidence_id: string;
    relationship_type: string;
    verification_status: string;
  }[];
  edges: ArgumentEdge[];
  conflicts: {
    edge_id: string;
    source_claim_id: string;
    target_claim_id: string;
    reason: string;
    timestamp: string;
  }[];
}

export interface PredictionMarket {
  id: string;
  case_id: string;
  case_version: number;
  question: string;
  outcome_definition: string;
  resolution_method: string;
  rubric_version: string;
  commit_deadline: string;
  reveal_deadline: string;
  resolution_deadline: string;
  challenge_window_seconds: number;
  scoring_version: string;
  void_criteria: string;
  status: 'DRAFT' | 'PUBLISHED' | 'REVEAL' | 'CLOSED' | 'RESOLUTION_PROPOSED' | 'CHALLENGE' | 'SETTLED' | 'VOID';
  contract_address: string;
  proposed_outcome: number | null;
  resolution_reference: string | null;
  evaluator_address: string;
  aggregate_probability: number;
  disagreement_variance: number;
  sample_size: number;
  created_at: string;
  forecasts: Forecast[];
}

export interface Forecast {
  id: string;
  market_id: string;
  agent_id: string;
  commitment_hash: string;
  probability: number | null;
  evidence_digest: string | null;
  nonce: string | null;
  reveal_status: 'COMMITTED' | 'REVEALED' | 'MISMATCH' | 'EXPIRED';
  commit_tx_hash: string | null;
  reveal_tx_hash: string | null;
  brier_score: number | null;
  created_at: string;
  revealed_at: string | null;
}

export interface EvidenceBounty {
  id: string;
  case_id: string;
  question: string;
  acceptance_criteria: string;
  reward_amount: number;
  deadline: string;
  challenge_window_seconds: number;
  status: 'CREATED' | 'FUNDED' | 'OPEN' | 'REVIEW' | 'CHALLENGE' | 'AWARDED' | 'REJECTED' | 'CANCELLED' | 'SETTLED';
  contract_reference: string;
  winning_submission_id: string | null;
  creator_address: string;
  created_at: string;
  submissions: EvidenceSubmission[];
}

export interface EvidenceSubmission {
  id: string;
  bounty_id: string;
  contributor_address: string;
  title: string;
  source_reference: string;
  content: string;
  digest: string;
  provenance: Record<string, any>;
  status: 'SUBMITTED' | 'UNDER_REVIEW' | 'ACCEPTED' | 'REJECTED' | 'CHALLENGED';
  review_reason: string | null;
  reviewer_address: string | null;
  submitted_at: string;
  reviewed_at: string | null;
}

export interface Agent {
  id: string;
  wallet_address: string;
  role: 'LEGAL_RESEARCHER' | 'LEGAL_INTERPRETER' | 'ADVERSARIAL_RESEARCHER' | 'EVIDENCE_VERIFIER' | 'QUANTITATIVE_FORECASTER' | 'COORDINATOR';
  model_provider_version: string;
  prompt_version: string;
  status: string;
  reputation_score: number;
  brier_score: number;
  sample_count: number;
  simulated_credits: number;
  created_at: string;
}

export interface AgentReputation {
  agent_id: string;
  wallet_address: string;
  role: string;
  reputation_score: number;
  brier_score: number;
  sample_count: number;
  simulated_credits: number;
  scoring_version: string;
  is_small_sample: boolean;
  reputation_weight: number;
}

export interface ReputationRecord {
  id: string;
  agent_id: string;
  delta: number;
  score_before: number;
  score_after: number;
  reason: string;
  event_reference: string;
  timestamp: string;
}

export interface AuditEvent {
  id: string;
  case_id: string;
  event_type: string;
  actor: string;
  payload_digest: string;
  payload: Record<string, any>;
  tx_hash: string | null;
  timestamp: string;
}

export interface FinalCaseReport {
  case_id: string;
  case_version: number;
  generated_at: string;
  section1_executive_summary: {
    case_id: string;
    case_version: number;
    title: string;
    jurisdiction: string;
    question: string;
    assessment_date: string;
    overall_risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    executive_summary_text: string;
  };
  section2_facts_and_assumptions: {
    facts: Record<string, any>;
    implicit_assumptions: string[];
    missing_facts_identified: string[];
  };
  section3_sources_and_dates: {
    sources: {
      id: string;
      title: string;
      authority: string;
      jurisdiction: string;
      effective_date: string;
      digest: string;
      url: string;
    }[];
  };
  section4_principal_claims: {
    claims: Claim[];
  };
  section5_counterarguments_and_conflicts: {
    counterarguments: { source: string; target: string; objection: string }[];
    detected_conflicts: { edge_id: string; source_claim_id: string; target_claim_id: string; reason: string }[];
  };
  section6_risk_findings: {
    findings: {
      rule_id: string;
      rule_name: string;
      statutory_reference: string;
      passed: boolean;
      violation_detected: boolean;
      severity: string;
      factual_trigger: string;
      legal_analysis: string;
      remedial_action: string;
    }[];
    confidence_limitations: string[];
  };
  section7_forecasts: {
    markets: {
      market_id: string;
      question: string;
      aggregate_probability: number;
      disagreement_variance: number;
      sample_size: number;
      status: string;
      proposed_outcome: number | null;
    }[];
  };
  section8_bounties_and_uncertainties: {
    unresolved_questions: { question: string; rule: string; statute: string; severity: string }[];
    bounties: { bounty_id: string; question: string; reward: number; status: string; winner: string | null }[];
  };
  section9_recommendations: {
    recommended_actions: string[];
    human_review_notice: string;
  };
  section10_audit_trail: {
    audit_events_count: number;
    recent_transactions: {
      event_type: string;
      actor: string;
      tx_hash: string | null;
      payload_digest: string;
      timestamp: string;
    }[];
  };
}
