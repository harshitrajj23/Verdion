export interface CaseData {
  id: string;
  title: string;
  jurisdiction: string;
  assessment_date: string;
  question: string;
  scope_version: number;
  status: string;
  facts: {
    processing_purpose: string;
    data_categories: string[];
    affected_users: string;
    retention_period_days?: number;
    automated_decision_making: boolean;
    user_consent_mechanism: string;
    safeguards: string[];
  };
  missing_facts: string[];
  source_corpus_version: string;
  provenance?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentMetric {
  agent_id: string;
  role: "LEGAL_RESEARCHER" | "LEGAL_INTERPRETER" | "ADVERSARIAL_RESEARCHER" | "EVIDENCE_VERIFIER" | "QUANTITATIVE_FORECASTER" | "COORDINATOR";
  name: string;
  status: "IDLE" | "ACTIVE" | "COMPLETED" | "FAILED" | "ABSTAINED";
  current_task: string;
  sources_consulted: number;
  claims_generated: number;
  counterarguments_count: number;
  forecast_prob?: number;
  uncertainty_score: number;
  elapsed_ms: number;
  token_usage: number;
  cost_usd: number;
  failures: string[];
  last_output_summary: string;
}

export interface GraphNode {
  id: string;
  type: "CLAIM" | "EVIDENCE" | "ASSUMPTION";
  label: string;
  agent?: string;
  evidence_status?: "SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED" | "QUALIFIED";
  digest?: string;
  authority?: string;
  effective_date?: string;
  details?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: "SUPPORT" | "CONTRADICTION" | "QUALIFY" | "DEPEND_ON" | "SUPERSEDE";
  reason: string;
}

export interface MarketData {
  market_id: string;
  case_id: string;
  case_version: number;
  question: string;
  outcome_definition: string;
  resolution_source: string;
  evaluator_address: string;
  commit_deadline: string;
  reveal_deadline: string;
  challenge_deadline: string;
  state: "DRAFT" | "PUBLISHED" | "REVEAL" | "CLOSED" | "RESOLUTION_PROPOSED" | "CHALLENGE" | "SETTLED" | "VOID";
  aggregate_probability: number;
  disagreement_variance: number;
  sample_size: number;
  reward_pool_credits: number;
  revealed_forecasts: {
    agent_id: string;
    agent_address: string;
    probability: number;
    evidence_digest: string;
    revealed_at: string;
    brier_score?: number;
  }[];
  challenge_status: {
    is_challenged: boolean;
    challenger?: string;
    reason?: string;
  };
  settlement_tx?: string;
  deadline_phase_label?: string;
  is_recorded_sepolia?: boolean;
}

export interface BountyData {
  bounty_id: string;
  case_id: string;
  question: string;
  reward_credits: number;
  deadline: string;
  state: "CREATED" | "FUNDED" | "OPEN" | "REVIEW" | "CHALLENGE" | "AWARDED" | "REJECTED" | "CANCELLED" | "SETTLED";
  acceptance_rubric: {
    criterion: string;
    weight: number;
    score?: number;
  }[];
  submissions: {
    submission_id: string;
    contributor: string;
    evidence_digest: string;
    source_title: string;
    passage_reference: string;
    quote: string;
    effective_date: string;
    submitted_at: string;
    is_accepted?: boolean;
    reviewer_reason?: string;
  }[];
  winning_submission_id?: string;
  challenge_deadline?: string;
  settlement_tx?: string;
  weighted_score?: number;
}

export interface AuditRecord {
  id: string;
  event_type: "CASE_CREATED" | "SCOPE_VERSIONED" | "EVIDENCE_ANCHORED" | "FORECAST_COMMITTED" | "FORECAST_REVEALED" | "RESOLUTION_PROPOSED" | "BOUNTY_OPENED" | "BOUNTY_SETTLED" | "SETTLEMENT_EXECUTED" | "AGENT_REGISTERED" | "MARKET_CREATED" | "MARKET_FUNDED" | "MARKET_PUBLISHED" | "MARKET_CLOSED";
  actor: string;
  target_id: string;
  payload_digest: string;
  tx_hash: string;
  timestamp: string;
  block_number: number;
  status: "CONFIRMED" | "PENDING" | "REVERTED";
  etherscan_url?: string;
  source_type?: "ON_CHAIN_RECORDED" | "SAMPLE_FIXTURE";
}

export interface BenchmarkResult {
  baseline_id: string;
  baseline_name: string;
  description: string;
  brier_all: number;
  brier_held_out: number;
  unsupported_claim_rate: number;
  f1_score: number;
  avg_latency_ms: number;
  cost_usd: number;
}
