import { CaseData, MarketData, BountyData, AuditRecord, AgentMetric } from "./mockData";

const API_BASE = typeof window !== "undefined" ? "/api/v1" : "http://127.0.0.1:8000/api/v1";

export interface CreateCasePayload {
  title: string;
  question: string;
  jurisdiction: string;
  assessment_date: string;
  facts: Record<string, any>;
}

export const api = {
  async getCases(): Promise<CaseData[]> {
    const res = await fetch(`${API_BASE}/cases`);
    if (!res.ok) throw new Error(`Failed to fetch cases: ${res.statusText}`);
    const data = await res.json();
    return data.map((c: any) => ({
      id: c.id,
      title: c.title,
      jurisdiction: c.jurisdiction,
      assessment_date: c.assessment_date,
      question: c.question,
      scope_version: c.scope_version,
      status: c.status,
      facts: c.facts || {},
      missing_facts: [],
      source_corpus_version: "2026.10-EU-GDPR",
      provenance: c.provenance || "OPERATIONAL",
      created_at: c.created_at,
      updated_at: c.updated_at
    }));
  },

  async createCase(payload: CreateCasePayload): Promise<CaseData> {
    const res = await fetch(`${API_BASE}/cases`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create case: ${res.statusText}`);
    }
    const created = await res.json();
    return this.getCase(created.caseId || created.id);
  },

  async getCase(caseId: string): Promise<CaseData> {
    const res = await fetch(`${API_BASE}/cases/${caseId}`);
    if (!res.ok) throw new Error(`Failed to fetch case ${caseId}`);
    const c = await res.json();
    return {
      id: c.id,
      title: c.title,
      jurisdiction: c.jurisdiction,
      assessment_date: c.assessment_date,
      question: c.question,
      scope_version: c.scope_version,
      status: c.status,
      facts: c.facts || {},
      missing_facts: [],
      source_corpus_version: "2026.10-EU-GDPR",
      provenance: c.provenance || "OPERATIONAL",
      created_at: c.created_at,
      updated_at: c.updated_at
    };
  },

  async analyzeCase(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${caseId}/analyze?sync=true`, {
      method: "POST"
    });
    if (!res.ok) throw new Error(`Failed to run analysis for case ${caseId}`);
    return await res.json();
  },

  async getMarkets(): Promise<MarketData[]> {
    const res = await fetch(`${API_BASE}/markets`);
    if (!res.ok) throw new Error(`Failed to fetch markets: ${res.statusText}`);
    const data = await res.json();
    return data.map((m: any) => ({
      market_id: m.id,
      case_id: m.case_id,
      case_version: m.case_version || 1,
      question: m.question,
      outcome_definition: m.outcome_definition,
      resolution_source: m.resolution_method || "Independent legal evaluator review",
      evaluator_address: m.evaluator_address,
      commit_deadline: m.commit_deadline,
      reveal_deadline: m.reveal_deadline,
      challenge_deadline: m.resolution_deadline,
      state: m.status,
      aggregate_probability: m.aggregate_probability || 0,
      disagreement_variance: m.disagreement_variance || 0,
      sample_size: m.sample_size || (m.forecasts ? m.forecasts.filter((f: any) => f.reveal_status === "REVEALED").length : 0),
      reward_pool_credits: 500,
      revealed_forecasts: (m.forecasts || [])
        .filter((f: any) => f.reveal_status === "REVEALED")
        .map((f: any) => ({
          agent_id: f.agent_id,
          agent_address: f.wallet_address || "0xAgent",
          probability: f.probability,
          evidence_digest: f.evidence_digest || "0x",
          revealed_at: f.revealed_at || f.created_at,
          brier_score: f.brier_score
        })),
      challenge_status: {
        is_challenged: m.status === "CHALLENGE",
        challenger: undefined,
        reason: undefined
      },
      settlement_tx: m.settlement_tx || undefined,
      is_recorded_sepolia: false
    }));
  },

  async commitForecast(marketId: string, payload: { agent_id: string; commitment_hash: string; wallet_address?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/markets/${marketId}/commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Forecast commitment failed");
    }
    return await res.json();
  },

  async revealForecast(marketId: string, payload: { agent_id: string; probability: number; evidence_digest: string; nonce: string; wallet_address?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/markets/${marketId}/reveal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Forecast reveal failed");
    }
    return await res.json();
  },

  async settleMarket(marketId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/markets/${marketId}/settle`, {
      method: "POST"
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Market settlement failed");
    }
    return await res.json();
  },

  async getBounties(): Promise<BountyData[]> {
    const res = await fetch(`${API_BASE}/bounties`);
    if (!res.ok) throw new Error(`Failed to fetch bounties: ${res.statusText}`);
    const data = await res.json();
    return data.map((b: any) => ({
      bounty_id: b.id,
      case_id: b.case_id,
      question: b.question,
      reward_credits: b.reward_amount || 100,
      deadline: b.deadline,
      state: b.status,
      acceptance_rubric: [
        { criterion: "Authority Jurisdiction (CJEU / EDPB / High Court)", weight: 0.35, score: 0.95 },
        { criterion: "Direct Statutory Applicability", weight: 0.35, score: 0.90 },
        { criterion: "Cryptographic Digest Hash Match", weight: 0.30, score: 1.0 }
      ],
      submissions: (b.submissions || []).map((s: any) => ({
        submission_id: s.id,
        contributor: s.contributor_address,
        evidence_digest: s.digest,
        source_title: s.title,
        passage_reference: s.source_reference,
        quote: s.content,
        effective_date: "2024-04-17",
        submitted_at: s.submitted_at,
        is_accepted: s.status === "ACCEPTED",
        reviewer_reason: s.review_reason
      })),
      winning_submission_id: b.winning_submission_id || undefined,
      settlement_tx: undefined,
      weighted_score: 0.94
    }));
  },

  async submitEvidence(bountyId: string, payload: { contributor_address: string; title: string; source_reference: string; content: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/bounties/${bountyId}/submissions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...payload,
        provenance: { submitted_via: "web_portal", verified: true }
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Evidence submission failed");
    }
    return await res.json();
  },

  async settleBounty(bountyId: string, winningSubmissionId: string, reviewReason: string): Promise<any> {
    const res = await fetch(`${API_BASE}/bounties/${bountyId}/settle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        winning_submission_id: winningSubmissionId,
        review_reason: reviewReason
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Bounty settlement failed");
    }
    return await res.json();
  },

  async getAuditRecords(): Promise<AuditRecord[]> {
    const res = await fetch(`${API_BASE}/audit`);
    if (!res.ok) throw new Error(`Failed to fetch audit trail: ${res.statusText}`);
    const data = await res.json();
    return data.map((a: any) => ({
      id: a.id,
      event_type: a.event_type,
      actor: a.actor,
      target_id: a.case_id || a.id,
      payload_digest: a.payload_digest,
      tx_hash: a.tx_hash || a.payload_digest,
      timestamp: a.timestamp,
      block_number: a.block_number || 5410520,
      status: a.status || "CONFIRMED"
    }));
  },

  async getAgents(): Promise<AgentMetric[]> {
    const res = await fetch(`${API_BASE}/agents`);
    if (!res.ok) throw new Error(`Failed to fetch agents: ${res.statusText}`);
    const data = await res.json();
    return data.map((ag: any) => ({
      agent_id: ag.id,
      role: ag.role,
      name: ag.role.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()),
      status: ag.status,
      current_task: `Specialized ${ag.role.toLowerCase()} operations under prompt version ${ag.prompt_version}`,
      sources_consulted: 5,
      claims_generated: 4,
      counterarguments_count: 2,
      uncertainty_score: 0.15,
      elapsed_ms: 120,
      token_usage: 1450,
      cost_usd: 0.002,
      failures: [],
      last_output_summary: `Reputation score: ${ag.reputation_score} | Brier score: ${ag.brier_score}`
    }));
  },

  async getIntegrationsStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/integrations/status`);
    if (!res.ok) throw new Error("Failed to fetch integrations status");
    return await res.json();
  },

  async verifyTransaction(txHash: string): Promise<any> {
    const res = await fetch(`${API_BASE}/integrations/verify-tx?tx_hash=${encodeURIComponent(txHash)}`);
    if (!res.ok) throw new Error("Failed to verify transaction on chain");
    return await res.json();
  },

  async getIngestionJobs(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/ingestion/jobs`);
    if (!res.ok) return [];
    return await res.json();
  },

  async triggerIngestion(adapter: string = "eur_lex", identifier?: string): Promise<any> {
    const url = identifier
      ? `${API_BASE}/ingestion/trigger?adapter=${encodeURIComponent(adapter)}&identifier=${encodeURIComponent(identifier)}`
      : `${API_BASE}/ingestion/trigger?adapter=${encodeURIComponent(adapter)}`;
    const res = await fetch(url, {
      method: "POST"
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Ingestion trigger failed");
    }
    return await res.json();
  },

  async getReanalysisProposals(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/ingestion/proposals`);
    if (!res.ok) return [];
    return await res.json();
  },

  async getSources(provenance?: string): Promise<any[]> {
    const url = provenance
      ? `${API_BASE}/sources?provenance=${encodeURIComponent(provenance)}`
      : `${API_BASE}/sources`;
    const res = await fetch(url);
    if (!res.ok) return [];
    return await res.json();
  },

  async getSourceDetail(sourceId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/ingestion/sources/${encodeURIComponent(sourceId)}`);
    if (!res.ok) throw new Error(`Failed to fetch source details for ${sourceId}`);
    return await res.json();
  },

  async getDecisionRecord(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/decision-record`);
    if (!res.ok) throw new Error("Failed to fetch decision record");
    return await res.json();
  },

  async getAuditPackage(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/cases/${encodeURIComponent(caseId)}/audit-package`);
    if (!res.ok) throw new Error("Failed to export audit package");
    return await res.json();
  },

  async verifyAuditChain(caseId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/chain/${encodeURIComponent(caseId)}`);
    if (!res.ok) throw new Error("Failed to verify audit chain");
    return await res.json();
  },

  async verifyAuditPackage(packageData: any): Promise<any> {
    const res = await fetch(`${API_BASE}/audit/verify-package`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(packageData)
    });
    if (!res.ok) throw new Error("Failed to verify audit package");
    return await res.json();
  },

  async getForecastingEvaluation(): Promise<any> {
    const res = await fetch(`${API_BASE}/markets/evaluation`);
    if (!res.ok) throw new Error("Failed to fetch forecasting evaluation");
    return await res.json();
  },

  async getCaseWorkspace(caseId: string, trustedCheckpoint?: string): Promise<any> {
    const url = trustedCheckpoint
      ? `${API_BASE}/cases/${encodeURIComponent(caseId)}/workspace?trusted_checkpoint=${encodeURIComponent(trustedCheckpoint)}`
      : `${API_BASE}/cases/${encodeURIComponent(caseId)}/workspace`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch case workspace: ${res.statusText}`);
    return await res.json();
  },

  async transitionWorkflow(caseId: string, targetState: string, reason?: string): Promise<any> {
    const url = `${API_BASE}/cases/${encodeURIComponent(caseId)}/workflow/transition?target_state=${encodeURIComponent(targetState)}${reason ? `&reason=${encodeURIComponent(reason)}` : ""}`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail?.message || err.detail || `Transition to ${targetState} failed`);
    }
    return await res.json();
  },

  async bindEvidence(caseId: string, queryOverride?: string): Promise<any> {
    const url = `${API_BASE}/cases/${encodeURIComponent(caseId)}/workflow/bind-evidence${queryOverride ? `?query_override=${encodeURIComponent(queryOverride)}` : ""}`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail?.message || err.detail || "Failed to bind evidence");
    }
    return await res.json();
  },

  async analyzeAndSealCase(caseId: string): Promise<any> {
    const url = `${API_BASE}/cases/${encodeURIComponent(caseId)}/workflow/analyze-and-seal`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail?.message || err.detail || "Failed to analyze and seal case");
    }
    return await res.json();
  },

  async finalizeAuditWorkflow(caseId: string, trustedCheckpoint?: string): Promise<any> {
    const url = trustedCheckpoint
      ? `${API_BASE}/cases/${encodeURIComponent(caseId)}/workflow/finalize-audit?trusted_checkpoint=${encodeURIComponent(trustedCheckpoint)}`
      : `${API_BASE}/cases/${encodeURIComponent(caseId)}/workflow/finalize-audit`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail?.message || err.detail || "Failed to finalize audit workflow");
    }
    return await res.json();
  }
};


