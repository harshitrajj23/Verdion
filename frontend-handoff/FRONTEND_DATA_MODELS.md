# VERIDION — Frontend TypeScript Data Models

The following TypeScript definitions match the backend Pydantic schemas:

```typescript
export interface Case {
  id: string;
  title: string;
  jurisdiction: "EU" | "US-CA" | "GLOBAL";
  status: "DRAFT" | "ANALYZING" | "COMPLETED" | "FAILED";
  scope_version: number;
  facts: Record<string, any>;
  assessment_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ConfidenceContract {
  raw_confidence: number;
  calibrated_confidence?: number;
  confidence_type: "RULE_DERIVED" | "MODEL_ESTIMATED" | "CRYPTOGRAPHIC_INTEGRITY" | "EMPIRICALLY_CALIBRATED" | "UNCALIBRATED";
  calibration_status: "UNCALIBRATED" | "HEURISTIC_BOUNDED" | "EMPIRICALLY_CALIBRATED";
  uncertainty_score: number;
  supporting_evidence_count: number;
  contradicting_evidence_count: number;
  inference_mode: string;
  model_identifier: string;
}

export interface EvidenceRef {
  evidence_id: string;
  passage_reference: string;
  digest: string;
  relationship?: "SUPPORTS" | "REFUTES" | "QUALIFIES";
  relevance_score?: number;
}

export interface Claim {
  id: string;
  claim_text: string;
  claim_type: "STATUTORY_INTERPRETATION" | "FACTUAL_MAPPING" | "RISK_ASSESSMENT" | "EXCEPTION";
  confidence: number;
  confidence_rationale: string;
  is_supported: boolean;
  evidence_refs: EvidenceRef[];
  confidence_contract?: ConfidenceContract;
}

export interface EvidencePassage {
  id: string;
  evidence_id: string;
  passage_reference: string;
  digest: string;
  text: string;
  jurisdiction: string;
  authority: string;
  provenance: string;
  effective_date?: string;
  url?: string;
}

export interface ClaimGroundingResult {
  overall_status: "VERIFIED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | "CONTRADICTED" | "UNVERIFIED" | "HUMAN_REVIEW_REQUIRED";
  dimension_statuses: Record<string, string>;
  dimension_scores: Record<string, number>;
  dimension_rationales: Record<string, string>;
  is_fully_grounded: boolean;
  requires_human_review: boolean;
  audit_notes: string[];
}

export interface CanonicalDecisionRecord {
  decision_id: string;
  case_id: string;
  case_version: number;
  record_digest: string;
  orchestration_version: string;
  software_version: string;
  analysis_timestamp: string;
  evidence_sources: any[];
  evidence_passages: EvidencePassage[];
  claims: Claim[];
  audit_events: any[];
}

export interface ForecastCommitment {
  id: string;
  market_id: string;
  agent_id: string;
  commitment_hash: string;
  probability?: number;
  evidence_digest?: string;
  nonce?: string;
  reveal_status: "COMMITTED" | "REVEALED" | "MISMATCH" | "EXPIRED";
  brier_score?: number;
  created_at: string;
  revealed_at?: string;
}

export interface AuditEvent {
  id: string;
  sequence_number: number;
  case_id: string;
  event_type: string;
  actor: string;
  payload: Record<string, any>;
  event_digest: string;
  previous_digest: string;
  timestamp: string;
}
```
