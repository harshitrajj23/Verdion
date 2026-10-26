"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import {
  Briefcase,
  Layers,
  FileText,
  AlertTriangle,
  CheckCircle2,
  GitFork,
  TrendingUp,
  Gift,
  ExternalLink,
  ShieldCheck,
  ChevronRight,
  Database,
  ArrowRight,
  Cpu,
  HelpCircle,
  Clock,
  Sparkles
} from "lucide-react";

export default function CaseWorkspacePage() {
  const { currentCase, markets, bounties, agents, isLiveChain } = useStore();
  const [activeTab, setActiveTab] = useState<"overview" | "facts" | "sources" | "agents" | "timeline">("overview");

  // Sample unresolved questions (§16.2)
  const unresolvedQuestions = [
    {
      id: "UQ-01",
      topic: "PII Anonymization Irreversibility",
      question: "Does the automated PII masking pipeline achieve true irreversibility under EDPB guidelines, or does residual semantic context enable re-identification?",
      status: "OPEN_BOUNTY",
      linkedBounty: "bounty_edpb_001"
    },
    {
      id: "UQ-02",
      topic: "Opt-Out Granularity",
      question: "Are end-users provided an affirmative, granular opt-out mechanism before conversational transcripts are committed to model training partitions?",
      status: "UNRESOLVED_FACT",
      linkedBounty: null
    },
    {
      id: "UQ-03",
      topic: "Statutory Defense Viability",
      question: "Can commercial AI refinement qualify under Article 6(1)(f) Legitimate Interests without an upfront Data Protection Impact Assessment (DPIA)?",
      status: "MARKET_EVALUATION",
      linkedBounty: null
    }
  ];

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* ── Case Header: Apple Store Utility Card ── */}
      <div className="apple-card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-5">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200">
                {currentCase.id}
              </span>
              <span className="text-xs text-ink-muted">
                Scope Version: <strong className="text-ink">{currentCase.scope_version}</strong> (Frozen)
              </span>
              <span className="text-xs text-ink-muted">
                Corpus Version: <strong className="text-lavender-700 font-mono">{currentCase.source_corpus_version}</strong>
              </span>
              <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-cream-200 text-ink-secondary">
                {isLiveChain ? "Live Chain Scope" : "Curated Benchmark Scope"}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-ink tracking-tight font-appleDisplay">
              {currentCase.title}
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3.5 py-1 rounded-full text-xs font-semibold bg-lavender-100 text-lavender-800 border border-lavender-200">
              {currentCase.status}
            </span>
          </div>
        </div>

        {/* Focal Investigative Question */}
        <div className="p-4 rounded-[14px] bg-cream-200/60 border border-cream-300 space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted block">
            Focal Investigative Question (§16.2):
          </span>
          <p className="text-sm font-normal text-ink leading-relaxed">
            {currentCase.question}
          </p>
        </div>

        {/* Apple Segmented Pill Tabs */}
        <div className="pt-2">
          <div className="inline-flex p-1 rounded-full bg-cream-200 border border-cream-300 max-w-full overflow-x-auto scrollbar-none">
            {(["overview", "facts", "sources", "agents", "timeline"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 text-xs rounded-full font-medium transition-all duration-150 active:scale-[0.97] whitespace-nowrap ${
                  activeTab === tab
                    ? "bg-white text-ink shadow-sm border border-cream-300/60"
                    : "text-ink-secondary hover:text-ink hover:bg-cream-100/60"
                }`}
              >
                {tab === "agents" ? "Agent Activity" : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tab Contents ── */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left (2 cols): Risk Findings & Missing Facts */}
          <div className="lg:col-span-2 space-y-6">
            {/* Missing Facts Card (FR-002) */}
            {currentCase.missing_facts.length > 0 && (
              <div className="apple-card space-y-3 border-amber-200 bg-amber-50/70">
                <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <h3>Missing Material Facts Detected (FR-002)</h3>
                </div>
                <p className="text-xs text-amber-800 leading-relaxed">
                  The scope validator requires explicit answers to these material factual gaps before a conclusive legal determination can be formulated:
                </p>
                <div className="space-y-2 pt-1">
                  {currentCase.missing_facts.map((mf, i) => (
                    <div
                      key={i}
                      className="p-3.5 rounded-[12px] bg-white border border-amber-200/80 text-xs text-amber-950 flex items-start gap-2.5"
                    >
                      <span className="font-mono text-amber-700 font-bold shrink-0">{i + 1}.</span>
                      <span>{mf}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Principal Findings Breakdown */}
            <div className="apple-card space-y-4">
              <h3 className="text-base font-semibold text-ink font-appleDisplay">
                Synthesized Risk Findings & Regulatory Status
              </h3>
              <div className="space-y-3">
                <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                      HIGH COMPLIANCE GAP
                    </span>
                    <span className="text-[11px] font-mono text-ink-muted">GDPR Art 6(4) / 5(1)(b)</span>
                  </div>
                  <p className="text-xs text-ink-secondary leading-relaxed">
                    Generic terms-of-service consent accepted during account signup does not fulfill the specificity standard required to repurpose conversational support logs for generative AI training.
                  </p>
                </div>

                <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-xs text-amber-800 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                      QUALIFIED DEFENSE IDENTIFIED
                    </span>
                    <span className="text-[11px] font-mono text-ink-muted">GDPR Art 6(1)(f) Recital 47</span>
                  </div>
                  <p className="text-xs text-ink-secondary leading-relaxed">
                    Adversarial Red Team demonstrated that service quality and safety improvement can be argued as a legitimate interest, provided automated pre-training PII scrubbers and user opt-outs are active.
                  </p>
                </div>
              </div>
            </div>

            {/* Unresolved Questions Panel (§16.2) */}
            <div className="apple-card space-y-4">
              <div className="flex items-center justify-between border-b border-cream-200 pb-3">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-lavender-600" />
                  <h3 className="text-base font-semibold text-ink font-appleDisplay">
                    Unresolved Questions & Inquiry Backlog (§16.2)
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-ink-muted">{unresolvedQuestions.length} Open Inquiries</span>
              </div>
              <div className="space-y-3">
                {unresolvedQuestions.map((uq) => (
                  <div key={uq.id} className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-lavender-100 text-lavender-800 border border-lavender-200">
                          {uq.id}
                        </span>
                        <span className="text-xs font-semibold text-ink">{uq.topic}</span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cream-200 text-ink-secondary">
                        {uq.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-ink-secondary leading-relaxed">{uq.question}</p>
                    {uq.linkedBounty && (
                      <div className="pt-1 flex items-center gap-2 text-xs text-lavender-700">
                        <Gift className="w-3.5 h-3.5" />
                        <Link href="/bounties" className="hover:underline flex items-center gap-1 font-medium">
                          <span>Evidence Bounty Created for this Question ({uq.linkedBounty})</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right (1 col): Linked Markets & Bounties */}
          <div className="space-y-6">
            <div className="apple-card space-y-4">
              <h3 className="text-sm font-semibold text-ink flex items-center gap-2 font-appleDisplay">
                <TrendingUp className="w-4 h-4 text-lavender-600" />
                <span>Linked Prediction Markets (§16.5)</span>
              </h3>
              <div className="space-y-3">
                {markets.map((m) => (
                  <div key={m.market_id} className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-lavender-700 font-semibold">{m.market_id}</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-100 text-lavender-800">
                        {m.state}
                      </span>
                    </div>
                    <p className="text-xs text-ink-secondary line-clamp-2">{m.question}</p>
                    <div className="flex items-center justify-between text-[11px] pt-1.5 border-t border-cream-200">
                      <span className="text-ink-muted">Consensus Probability:</span>
                      <span className="font-mono font-bold text-lavender-700">
                        {(m.aggregate_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <Link
                href="/markets"
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>Go to Prediction Markets</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </Link>
            </div>

            <div className="apple-card space-y-4">
              <h3 className="text-sm font-semibold text-ink flex items-center gap-2 font-appleDisplay">
                <Gift className="w-4 h-4 text-lavender-600" />
                <span>Linked Evidence Bounties (§16.6)</span>
              </h3>
              <div className="space-y-3">
                {bounties.map((b) => (
                  <div key={b.bounty_id} className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-ink font-semibold">{b.bounty_id}</span>
                      <span className="text-lavender-700 font-bold font-mono">+{b.reward_credits} Credits</span>
                    </div>
                    <p className="text-xs text-ink-secondary line-clamp-2">{b.question}</p>
                  </div>
                ))}
              </div>
              <Link
                href="/bounties"
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>Go to Evidence Bounties</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </Link>
            </div>

            {/* Argument Graph Shortcut */}
            <div className="apple-card space-y-3">
              <div className="flex items-center gap-2 text-lavender-700 font-semibold text-sm">
                <GitFork className="w-4 h-4" />
                <span>Argument Graph (§16.4)</span>
              </div>
              <p className="text-xs text-ink-secondary leading-relaxed">
                Inspect structured dialectic tree connecting statutory evidence, claims, and counter-arguments.
              </p>
              <Link
                href="/graph"
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>Open Graph Explorer</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === "facts" && (
        <div className="apple-card space-y-4">
          <h3 className="text-base font-semibold text-ink font-appleDisplay">Frozen Case Facts (§14)</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Processing Purpose:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.processing_purpose}</p>
            </div>
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Affected Users:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.affected_users}</p>
            </div>
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Consent Mechanism:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.user_consent_mechanism}</p>
            </div>
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-1">
              <span className="text-ink-muted">Retention Period:</span>
              <p className="font-semibold text-ink text-sm">{currentCase.facts.retention_period_days} Days</p>
            </div>
            <div className="sm:col-span-2 p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-2">
              <span className="text-ink-muted">Data Categories Ingested:</span>
              <div className="flex flex-wrap gap-2">
                {currentCase.facts.data_categories.map((cat, i) => (
                  <span key={i} className="px-3 py-1 rounded-full bg-lavender-100 text-lavender-800 text-xs font-mono">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "sources" && (
        <div className="apple-card space-y-4">
          <h3 className="text-base font-semibold text-ink font-appleDisplay">
            Curated Source Collection & Effective Dates (FR-006, FR-007)
          </h3>
          <div className="space-y-3">
            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 flex items-start justify-between gap-4 text-xs">
              <div className="space-y-1">
                <span className="font-mono text-lavender-700 font-semibold">gdpr_reg_2016_679</span>
                <h4 className="font-semibold text-ink text-sm">Regulation (EU) 2016/679 (GDPR)</h4>
                <p className="text-ink-secondary">Article 5(1)(b) Purpose Limitation & Article 6(4) Compatibility Test</p>
              </div>
              <div className="text-right shrink-0">
                <span className="px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200 text-[10px] font-semibold">
                  ACTIVE
                </span>
                <p className="text-[10px] text-ink-muted mt-1">Eff: 2018-05-25</p>
              </div>
            </div>

            <div className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 flex items-start justify-between gap-4 text-xs">
              <div className="space-y-1">
                <span className="font-mono text-lavender-700 font-semibold">edpb_statement_01_2024</span>
                <h4 className="font-semibold text-ink text-sm">EDPB Statement 01/2024 on Generative AI Model Development</h4>
                <p className="text-ink-secondary">Paragraph 4: Repurposing support transcripts for LLM fine-tuning</p>
              </div>
              <div className="text-right shrink-0">
                <span className="px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200 text-[10px] font-semibold">
                  ACTIVE
                </span>
                <p className="text-[10px] text-ink-muted mt-1">Eff: 2024-04-17</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "agents" && (
        <div className="apple-card space-y-4">
          <div className="flex items-center justify-between border-b border-cream-200 pb-3">
            <div>
              <h3 className="text-base font-semibold text-ink font-appleDisplay">
                Swarm Agent Activity Summary (§16.2, §16.3)
              </h3>
              <p className="text-xs text-ink-muted">Inspect the specialized autonomous nodes participating in this case investigation.</p>
            </div>
            <Link
              href="/agents"
              className="text-xs font-semibold text-lavender-700 hover:text-lavender-900 flex items-center gap-1"
            >
              <span>Full Agent Lab</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((ag) => (
              <div
                key={ag.agent_id}
                className="p-4 rounded-[14px] bg-cream-50 border border-cream-300 space-y-3 hover:border-lavender-300 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-semibold text-lavender-700">{ag.role}</span>
                  <span className="px-2 py-0.5 rounded-full text-[9px] font-semibold bg-lavender-100 text-lavender-800">
                    {ag.status}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-ink">{ag.name}</h4>
                  <p className="text-xs text-ink-secondary line-clamp-2 mt-1">{ag.current_task}</p>
                </div>
                <div className="flex items-center justify-between text-[11px] pt-2 border-t border-cream-200 text-ink-muted">
                  <span>Claims: <strong className="text-ink font-mono">{ag.claims_generated}</strong></span>
                  <span>Uncertainty: <strong className="text-lavender-700 font-mono">{(ag.uncertainty_score * 100).toFixed(0)}%</strong></span>
                  <Link
                    href={`/agents?role=${ag.role}`}
                    className="text-lavender-700 hover:underline flex items-center gap-0.5 font-medium"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "timeline" && (
        <div className="apple-card space-y-4">
          <h3 className="text-base font-semibold text-ink font-appleDisplay">Autonomous Agent Activity Timeline</h3>
          <div className="space-y-4 border-l-2 border-cream-300 pl-4 ml-2">
            {agents.map((ag) => (
              <div key={ag.agent_id} className="relative space-y-1">
                <div className="absolute -left-[23px] top-1.5 w-3 h-3 rounded-full bg-lavender-600 border-2 border-white"></div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-ink">{ag.name}</span>
                  <span className="text-[10px] font-mono text-ink-muted">{ag.elapsed_ms}ms</span>
                </div>
                <p className="text-xs text-ink-secondary">{ag.current_task}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

