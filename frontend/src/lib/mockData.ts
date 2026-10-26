export interface CaseData {
  id: string;
  title: string;
  jurisdiction: string;
  assessment_date: string;
  question: string;
  scope_version: number;
  status: "DRAFT" | "RETRIEVAL" | "ANALYSIS" | "INVESTIGATION" | "REVIEW" | "COMPLETED" | "FAILED";
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
  /** Optional: human-readable phase label derived from deadlines */
  deadline_phase_label?: string;
  /** Provenance indicator: true if this record reflects on-chain Sepolia execution */
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
  /** Optional: pre-computed weighted rubric score (0-1) */
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
  /** Optional: direct Etherscan link */
  etherscan_url?: string;
  /** Provenance tag to distinguish recorded on-chain testnet data from mock fixtures */
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

export const initialCase: CaseData = {
  id: "case_euaia_001",
  title: "AI Customer Support Analytics & Secondary Model Training",
  jurisdiction: "European Union",
  assessment_date: "2026-03-15",
  question: "Does secondary processing of unredacted customer support transcripts for generative AI model fine-tuning constitute an incompatible purpose under GDPR Article 6(4) / Article 5(1)(b) absent explicit renewed consent?",
  scope_version: 1,
  status: "INVESTIGATION",
  facts: {
    processing_purpose: "Customer support AI fine-tuning and sentiment analytics",
    data_categories: [
      "Customer support conversation transcripts",
      "User account identifiers",
      "Timestamp & session metadata"
    ],
    affected_users: "All active EU platform users (approx. 450,000 subjects)",
    retention_period_days: 365,
    automated_decision_making: false,
    user_consent_mechanism: "General clickwrap Terms of Service acceptance at account creation",
    safeguards: ["Encryption at rest", "Restricted internal engineer access"]
  },
  missing_facts: [
    "No specific retention schedule defined for raw vector embeddings derived from conversations",
    "No pre-training automated PII redaction pipeline documented before model ingestion"
  ],
  source_corpus_version: "2026.1.0-EU-AIACT-GDPR",
  created_at: "2026-03-15T09:30:00Z",
  updated_at: "2026-03-15T10:15:00Z"
};

export const initialAgents: AgentMetric[] = [
  {
    agent_id: "agent_legal_researcher",
    role: "LEGAL_RESEARCHER",
    name: "Statutory Researcher",
    status: "COMPLETED",
    current_task: "Retrieved Article 5(1)(b), Article 6(4), and EDPB Statement 01/2024",
    sources_consulted: 4,
    claims_generated: 3,
    counterarguments_count: 0,
    uncertainty_score: 0.35,
    elapsed_ms: 540,
    token_usage: 520,
    cost_usd: 0.0015,
    failures: [],
    last_output_summary: "Confirmed 3 primary statutory articles active as of 2026-03-15. No superseded provisions identified."
  },
  {
    agent_id: "agent_legal_interpreter",
    role: "LEGAL_INTERPRETER",
    name: "Regulatory Interpreter",
    status: "COMPLETED",
    current_task: "Mapped facts against Article 6(4) purpose compatibility tests",
    sources_consulted: 3,
    claims_generated: 4,
    counterarguments_count: 1,
    uncertainty_score: 0.65,
    elapsed_ms: 680,
    token_usage: 640,
    cost_usd: 0.0021,
    failures: [],
    last_output_summary: "Deterministic rule check flagged HIGH_COMPLIANCE_GAP: generic ToS fails specificity requirement for LLM training."
  },
  {
    agent_id: "agent_adversarial",
    role: "ADVERSARIAL_RESEARCHER",
    name: "Adversarial Red Team",
    status: "COMPLETED",
    current_task: "Formulated legitimate interest defense under Article 6(1)(f) and Recital 47",
    sources_consulted: 2,
    claims_generated: 2,
    counterarguments_count: 3,
    uncertainty_score: 0.50,
    elapsed_ms: 490,
    token_usage: 480,
    cost_usd: 0.0016,
    failures: [],
    last_output_summary: "Contended model safety optimization is legitimate interest, but noted strict burden of proof under EDPB guidance."
  },
  {
    agent_id: "agent_verifier",
    role: "EVIDENCE_VERIFIER",
    name: "Integrity & Provenance Verifier",
    status: "COMPLETED",
    current_task: "Verified cryptographic digests for 4 cited passages",
    sources_consulted: 4,
    claims_generated: 1,
    counterarguments_count: 0,
    uncertainty_score: 0.20,
    elapsed_ms: 410,
    token_usage: 410,
    cost_usd: 0.0012,
    failures: [],
    last_output_summary: "3 passages verified against on-chain corpus digest. 1 claim marked UNSUPPORTED for missing exact paragraph citation."
  },
  {
    agent_id: "agent_forecaster_01",
    role: "QUANTITATIVE_FORECASTER",
    name: "Probabilistic Forecaster",
    status: "COMPLETED",
    current_task: "Generated probability distribution for independent benchmark evaluation",
    sources_consulted: 3,
    claims_generated: 1,
    counterarguments_count: 0,
    forecast_prob: 0.65,
    uncertainty_score: 0.65,
    elapsed_ms: 390,
    token_usage: 390,
    cost_usd: 0.0011,
    failures: [],
    last_output_summary: "Forecasted 65% likelihood that evaluator finds material compliance gap. Committed to PredictionMarket on-chain."
  },
  {
    agent_id: "agent_coordinator",
    role: "COORDINATOR",
    name: "Swarm Consensus Coordinator",
    status: "ACTIVE",
    current_task: "Ranking unresolved questions and structuring evidence bounties",
    sources_consulted: 5,
    claims_generated: 2,
    counterarguments_count: 2,
    uncertainty_score: 0.70,
    elapsed_ms: 510,
    token_usage: 450,
    cost_usd: 0.0013,
    failures: [],
    last_output_summary: "Identified top uncertainty: Priority 0.535. Formulated 100 simulated credit bounty for EDPB secondary processing precedents."
  }
];

export const initialGraphNodes: GraphNode[] = [
  {
    id: "n_claim_purpose",
    type: "CLAIM",
    label: "LLM fine-tuning represents a distinct, secondary purpose requiring independent lawful basis",
    agent: "Regulatory Interpreter",
    evidence_status: "SUPPORTED",
    details: "Generic terms of service consent does not fulfill the requirement for specific, informed consent under GDPR Article 6(1)(a) for training generative AI foundation models."
  },
  {
    id: "n_claim_legit_interest",
    type: "CLAIM",
    label: "Model improvement qualifies as legitimate interest under Article 6(1)(f) to improve service quality",
    agent: "Adversarial Red Team",
    evidence_status: "QUALIFIED",
    details: "Argues service performance, latency reduction, and automated safety filtering fall within legitimate expectations of commercial users."
  },
  {
    id: "n_claim_retention_gap",
    type: "CLAIM",
    label: "Storage limitation violated due to lack of defined schedule for derived vector embeddings",
    agent: "Regulatory Interpreter",
    evidence_status: "CONTRADICTED",
    details: "Indefinite storage of unredacted embeddings violates Article 5(1)(e)."
  },
  {
    id: "n_evi_art6_4",
    type: "EVIDENCE",
    label: "GDPR Article 6(4) Compatibility Criteria",
    authority: "European Parliament & Council",
    effective_date: "2018-05-25",
    digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
    details: "Requires assessment of relationship between purposes, context of collection, nature of data, and existence of appropriate safeguards such as pseudonymisation."
  },
  {
    id: "n_evi_edpb_stmt",
    type: "EVIDENCE",
    label: "EDPB Statement 01/2024 Para 4",
    authority: "European Data Protection Board",
    effective_date: "2024-04-17",
    digest: "0x34a178bc901e92837190ef2918bb1294819024ab719284910a82710398bbfa01",
    details: "Explicitly states that training or fine-tuning foundation models on user support logs represents a distinct purpose requiring standalone justification."
  },
  {
    id: "n_assumption_unredacted",
    type: "ASSUMPTION",
    label: "Assumption: Chat logs contain unredacted names and personal identifiers",
    agent: "Regulatory Interpreter",
    details: "Pending confirmation from data engineering whether PII scrubber is operational in staging."
  }
];

export const initialGraphEdges: GraphEdge[] = [
  {
    id: "e1",
    source: "n_evi_art6_4",
    target: "n_claim_purpose",
    relationship: "SUPPORT",
    reason: "Article 6(4) establishes strict compatibility conditions that are not met by routine service delivery consent."
  },
  {
    id: "e2",
    source: "n_evi_edpb_stmt",
    target: "n_claim_purpose",
    relationship: "SUPPORT",
    reason: "EDPB specifically designates AI model fine-tuning as an incompatible secondary purpose without safeguards."
  },
  {
    id: "e3",
    source: "n_claim_legit_interest",
    target: "n_claim_purpose",
    relationship: "CONTRADICTION",
    reason: "Adversarial hypothesis asserts Article 6(1)(f) legitimate interest overrides incompatibility finding."
  },
  {
    id: "e4",
    source: "n_claim_purpose",
    target: "n_claim_retention_gap",
    relationship: "DEPEND_ON",
    reason: "Retention violation severity directly amplifies secondary purpose incompatibility risk."
  },
  {
    id: "e5",
    source: "n_assumption_unredacted",
    target: "n_claim_purpose",
    relationship: "QUALIFY",
    reason: "If logs are fully anonymized prior to ingestion, GDPR purpose limitation rules cease to apply."
  }
];

export const initialMarkets: MarketData[] = [
  {
    market_id: "0x28ae...5b3e (Sepolia Lifecycle)",
    case_id: "0xe3a5...4df1",
    case_version: 1,
    question: "Did data processing comply with GDPR Article 6(1)(f) legitimate interest requirements for training AI models?",
    outcome_definition: "Resolves YES (1) if processing meets EDPB legitimate interest criteria; NO (0) otherwise. Settled on Sepolia Testnet via proper scoring rubric.",
    resolution_source: "Sepolia Testnet Evaluator (0x3486...2888)",
    evaluator_address: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    commit_deadline: "2026-03-15T12:00:00Z",
    reveal_deadline: "2026-03-15T12:05:00Z",
    challenge_deadline: "2026-03-15T12:10:00Z",
    state: "SETTLED",
    aggregate_probability: 0.65,
    disagreement_variance: 0.0,
    sample_size: 1,
    reward_pool_credits: 1000,
    revealed_forecasts: [
      {
        agent_id: "deployer_agent (Single Deployer Demo)",
        agent_address: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
        probability: 0.65,
        evidence_digest: "0xb798544e39396e624c9c1b7529433ff9ee69a48f4b00ce994ff37b25208466ff",
        revealed_at: "2026-03-15T12:04:00Z",
        brier_score: 0.1225
      }
    ],
    challenge_status: {
      is_challenged: false
    },
    settlement_tx: "0x220d460591302025e7f12d621399e2ab15724979678b4aed92ec2d2970e989e4",
    is_recorded_sepolia: true
  },
  {
    market_id: "mkt_gdpr_001",
    case_id: "case_euaia_001",
    case_version: 1,
    question: "Will the independent evaluator identify at least one material, unresolved GDPR Article 6(4) compliance gap?",
    outcome_definition: "Resolves YES (1) if evaluator determines that secondary AI model training on support transcripts lacks a valid lawful basis; resolves NO (0) if legitimate interest safeguards are deemed sufficient.",
    resolution_source: "Verdion Pre-Registered Benchmark Evaluator Rubric v1.0",
    evaluator_address: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    commit_deadline: "2026-03-15T14:00:00Z",
    reveal_deadline: "2026-03-15T18:00:00Z",
    challenge_deadline: "2026-03-16T18:00:00Z",
    state: "REVEAL",
    aggregate_probability: 0.633, // 63.3% unweighted mean (§9.2)
    disagreement_variance: 0.0205, // Disagreement variance (§9.3)
    sample_size: 3,
    reward_pool_credits: 500,
    revealed_forecasts: [
      {
        agent_id: "agent_forecaster_01",
        agent_address: "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        probability: 0.80,
        evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
        revealed_at: "2026-03-15T14:15:20Z"
      },
      {
        agent_id: "agent_forecaster_02",
        agent_address: "0x90F79bf6EB2c4f870365E785982E1f101E93b906",
        probability: 0.65,
        evidence_digest: "0x34a178bc901e92837190ef2918bb1294819024ab719284910a82710398bbfa01",
        revealed_at: "2026-03-15T14:22:10Z"
      },
      {
        agent_id: "agent_forecaster_03",
        agent_address: "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65",
        probability: 0.45,
        evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
        revealed_at: "2026-03-15T14:35:45Z"
      }
    ],
    challenge_status: {
      is_challenged: false
    },
    is_recorded_sepolia: false
  },
  {
    market_id: "mkt_retention_002",
    case_id: "case_euaia_001",
    case_version: 1,
    question: "Will indefinite storage of raw vector embeddings trigger an Article 5(1)(e) violation finding?",
    outcome_definition: "Resolves YES if unredacted embeddings retained over 180 days are deemed non-compliant.",
    resolution_source: "Independent Audit Benchmark Rubric",
    evaluator_address: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    commit_deadline: "2026-03-14T12:00:00Z",
    reveal_deadline: "2026-03-14T16:00:00Z",
    challenge_deadline: "2026-03-15T00:00:00Z",
    state: "SETTLED",
    aggregate_probability: 0.88,
    disagreement_variance: 0.0032,
    sample_size: 4,
    reward_pool_credits: 400,
    revealed_forecasts: [
      {
        agent_id: "agent_forecaster_01",
        agent_address: "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
        probability: 0.90,
        evidence_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
        revealed_at: "2026-03-14T14:00:00Z",
        brier_score: 0.0100
      }
    ],
    challenge_status: {
      is_challenged: false
    },
    settlement_tx: "0xd8a9140283fbd19842a9bcf01248ba09148bcae91823901bca819047190bc129",
    is_recorded_sepolia: false
  }
];

export const initialBounties: BountyData[] = [
  {
    bounty_id: "bounty_edpb_001",
    case_id: "case_euaia_001",
    question: "Authoritative regulatory decision or CJEU case law directly addressing whether training general-purpose LLMs on customer support chat logs requires refreshed specific consent under GDPR Art 6(4).",
    reward_credits: 100,
    deadline: "2026-03-16T12:00:00Z",
    state: "CHALLENGE",
    acceptance_rubric: [
      { criterion: "Source Authenticity and Provenance (20%)", weight: 0.20, score: 0.95 },
      { criterion: "Relevance to Exact Research Question (25%)", weight: 0.25, score: 0.90 },
      { criterion: "Jurisdictional Applicability & Effective Date (20%)", weight: 0.20, score: 0.85 },
      { criterion: "Reproducibility & Exact Passage Citation (15%)", weight: 0.15, score: 0.90 },
      { criterion: "Novelty Relative to Existing Evidence (10%)", weight: 0.10, score: 0.80 },
      { criterion: "Demonstrable Effect on Uncertainty (10%)", weight: 0.10, score: 0.85 }
    ],
    submissions: [
      {
        submission_id: "sub_edpb_001",
        contributor: "0x2546BcD3c84621e976D8185a91A922aE77ECEc30",
        evidence_digest: "0x34a178bc901e92837190ef2918bb1294819024ab719284910a82710398bbfa01",
        source_title: "EDPB Statement 01/2024 on Data Protection and Generative AI",
        passage_reference: "Section 3.2, Paragraph 4",
        quote: "Service providers repurposing user communication transcripts for foundation model fine-tuning cannot presume compatibility with contract execution purposes.",
        effective_date: "2024-04-17",
        submitted_at: "2026-03-15T11:00:00Z",
        is_accepted: true,
        reviewer_reason: "Directly addresses exact uncertainty regarding secondary training; verified active authority from official EDPB register."
      }
    ],
    winning_submission_id: "sub_edpb_001",
    challenge_deadline: "2026-03-16T18:00:00Z"
  }
];

export const initialAuditRecords: AuditRecord[] = [
  // ── Verified On-Chain Sepolia Lifecycle Transaction Receipts (§16.7) ──
  {
    id: "aud_sep_09",
    event_type: "SETTLEMENT_EXECUTED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0x220d460591302025e7f12d621399e2ab15724979678b4aed92ec2d2970e989e4",
    tx_hash: "0x220d460591302025e7f12d621399e2ab15724979678b4aed92ec2d2970e989e4",
    timestamp: "2026-03-15T12:12:00Z",
    block_number: 11997718,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_08",
    event_type: "RESOLUTION_PROPOSED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0x540fa04a63548c7d86e8dfbef3342e7dfd2daab82e77bbd9efcd5a0a0c8c9f52",
    tx_hash: "0x540fa04a63548c7d86e8dfbef3342e7dfd2daab82e77bbd9efcd5a0a0c8c9f52",
    timestamp: "2026-03-15T12:08:00Z",
    block_number: 11997482,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_07",
    event_type: "FORECAST_REVEALED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0xc6365643831ced46cc294393283e1f06f7128f30b564c42edbe8ca8126764815",
    tx_hash: "0xc6365643831ced46cc294393283e1f06f7128f30b564c42edbe8ca8126764815",
    timestamp: "2026-03-15T12:05:00Z",
    block_number: 11997472,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_06",
    event_type: "MARKET_CLOSED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0xaadb64b6f1ecbb49c58487838c62d55bbbc2c1b168b869678e7f07f310b055b1",
    tx_hash: "0xaadb64b6f1ecbb49c58487838c62d55bbbc2c1b168b869678e7f07f310b055b1",
    timestamp: "2026-03-15T12:04:00Z",
    block_number: 11997471,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_05",
    event_type: "FORECAST_COMMITTED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0xb6adb372a41a4b5e2a8d9f0c432ad27df62175f0dc7d67dc0bc0b850ace4908e",
    tx_hash: "0xb6adb372a41a4b5e2a8d9f0c432ad27df62175f0dc7d67dc0bc0b850ace4908e",
    timestamp: "2026-03-15T12:02:00Z",
    block_number: 11997464,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_04",
    event_type: "MARKET_PUBLISHED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0x104054e7082b47a7b262c9b552d0efd294e3521a3bea7e3ce8aa9a6627b1a6ae",
    tx_hash: "0x104054e7082b47a7b262c9b552d0efd294e3521a3bea7e3ce8aa9a6627b1a6ae",
    timestamp: "2026-03-15T12:01:30Z",
    block_number: 11997463,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_03",
    event_type: "MARKET_FUNDED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0x2a993f2f2668116ff7ab0e6c4bb70a233aefd325aaa71db90fafa12f524e86e5",
    tx_hash: "0x2a993f2f2668116ff7ab0e6c4bb70a233aefd325aaa71db90fafa12f524e86e5",
    timestamp: "2026-03-15T12:01:00Z",
    block_number: 11997462,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_02",
    event_type: "MARKET_CREATED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "0x28ae...5b3e",
    payload_digest: "0xf5588b6c9bb37e63df3937cf9f4bb3e3e99140442596aa76b562d4578ad0c1c7",
    tx_hash: "0xf5588b6c9bb37e63df3937cf9f4bb3e3e99140442596aa76b562d4578ad0c1c7",
    timestamp: "2026-03-15T12:00:30Z",
    block_number: 11997461,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  {
    id: "aud_sep_01",
    event_type: "AGENT_REGISTERED",
    actor: "0x34867B3Ad7B4353BA08bD74664E8bF27836e2888",
    target_id: "agent_deployer",
    payload_digest: "0x1f94f5085df2191495baf81a448bdc4d7965649e98e5177f11c494d7c0525d11",
    tx_hash: "0x1f94f5085df2191495baf81a448bdc4d7965649e98e5177f11c494d7c0525d11",
    timestamp: "2026-03-15T11:58:00Z",
    block_number: 11997418,
    status: "CONFIRMED",
    source_type: "ON_CHAIN_RECORDED"
  },
  // ── Sample Benchmark Fixtures (Client-Side Simulations) ──
  {
    id: "aud_demo_01",
    event_type: "CASE_CREATED",
    actor: "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    target_id: "case_euaia_001",
    payload_digest: "0xa1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
    tx_hash: "0x1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef01",
    timestamp: "2026-03-15T09:30:12Z",
    block_number: 5410291,
    status: "CONFIRMED",
    source_type: "SAMPLE_FIXTURE"
  },
  {
    id: "aud_demo_02",
    event_type: "EVIDENCE_ANCHORED",
    actor: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    target_id: "pas_gdpr_art6_4",
    payload_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
    tx_hash: "0x2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0123",
    timestamp: "2026-03-15T10:05:40Z",
    block_number: 5410310,
    status: "CONFIRMED",
    source_type: "SAMPLE_FIXTURE"
  },
  {
    id: "aud_demo_03",
    event_type: "FORECAST_COMMITTED",
    actor: "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    target_id: "mkt_gdpr_001",
    payload_digest: "0x7a8b9c0d1e2f3a4b5c6d7e8f90123456789abcdef0123456789abcdef0123456",
    tx_hash: "0x3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef012345",
    timestamp: "2026-03-15T13:45:00Z",
    block_number: 5410450,
    status: "CONFIRMED",
    source_type: "SAMPLE_FIXTURE"
  },
  {
    id: "aud_demo_04",
    event_type: "FORECAST_REVEALED",
    actor: "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
    target_id: "mkt_gdpr_001",
    payload_digest: "0x8fa12b9c3f4e8891d09e7284cb9124a919248bb82948019a827401bbac901842",
    tx_hash: "0x4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef01234567",
    timestamp: "2026-03-15T14:15:20Z",
    block_number: 5410495,
    status: "CONFIRMED",
    source_type: "SAMPLE_FIXTURE"
  },
  {
    id: "aud_demo_05",
    event_type: "BOUNTY_OPENED",
    actor: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
    target_id: "bounty_edpb_001",
    payload_digest: "0x5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0123456789",
    tx_hash: "0x5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0123456789",
    timestamp: "2026-03-15T10:45:00Z",
    block_number: 5410342,
    status: "CONFIRMED",
    source_type: "SAMPLE_FIXTURE"
  }
];

export const mockContractAddresses = {
  chainId: 11155111, // Sepolia Testnet
  networkName: "Ethereum Sepolia Testnet",
  CaseRegistry: "0x9dEEFCa6b93d9812Cf67Dc7b3daCc51b62C6455E",
  AgentRegistry: "0x32d5D291e287fF173F803f5ee53Aef75BADb2006",
  PredictionMarket: "0xFF5e85547E443e3d50b393E09885c6Eb9671EE27",
  EvidenceBounty: "0xF9805f322ccB6f25f1FAD9266DA9420DC2595a46",
  ReputationSettlement: "0xb002cd06fC2ce01B38C08787E6C4EaeAf547748c"
};
