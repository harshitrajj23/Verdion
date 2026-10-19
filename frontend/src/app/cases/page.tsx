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
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Case Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                {currentCase.id}
              </span>
              <span className="text-xs text-slate-400">
                Scope Version: <strong className="text-white">{currentCase.scope_version}</strong> (Frozen)
              </span>
              <span className="text-xs text-slate-400">
                Corpus Version: <strong className="text-cyan-400">{currentCase.source_corpus_version}</strong>
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                {isLiveChain ? "Live Chain Scope" : "Curated Benchmark Scope"}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-white">{currentCase.title}</h1>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-950 text-cyan-300 border border-cyan-500/40">
              {currentCase.status}
            </span>
          </div>
        </div>

        {/* Investigative Question */}
        <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Focal Investigative Question (§16.2):
          </span>
          <p className="text-sm font-medium text-slate-200 leading-relaxed">
            {currentCase.question}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-slate-800/80 pt-2 overflow-x-auto">
          {(["overview", "facts", "sources", "agents", "timeline"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-xs font-semibold capitalize border-b-2 transition-all whitespace-nowrap ${
                activeTab === tab
                  ? "border-emerald-400 text-emerald-300 bg-emerald-500/5"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab === "agents" ? "Agent Activity" : tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Contents */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left (2 cols): Risk Findings & Missing Facts */}
          <div className="lg:col-span-2 space-y-6">
            {/* Missing Facts Card (FR-002) */}
            {currentCase.missing_facts.length > 0 && (
              <div className="glass-panel p-6 rounded-3xl space-y-3 border-amber-900/40 bg-amber-950/10">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  <h3>Missing Material Facts Detected (FR-002)</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  The scope validator requires explicit answers to these material factual gaps before a conclusive legal determination can be formulated:
                </p>
                <div className="space-y-2 pt-1">
                  {currentCase.missing_facts.map((mf, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-950/60 border border-amber-800/30 text-xs text-amber-200/90 flex items-start gap-2.5"
                    >
                      <span className="font-mono text-amber-400 font-bold shrink-0">{i + 1}.</span>
                      <span>{mf}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Principal Findings Breakdown */}
            <div className="glass-panel p-6 rounded-3xl space-y-4">
              <h3 className="text-sm font-bold text-white">Synthesized Risk Findings & Regulatory Status</h3>
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-rose-400">HIGH COMPLIANCE GAP</span>
                    <span className="text-[10px] font-mono text-slate-400">GDPR Art 6(4) / 5(1)(b)</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Generic terms-of-service consent accepted during account signup does not fulfill the specificity standard required to repurpose conversational support logs for generative AI training.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-amber-400">QUALIFIED DEFENSE IDENTIFIED</span>
                    <span className="text-[10px] font-mono text-slate-400">GDPR Art 6(1)(f) Recital 47</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Adversarial Red Team demonstrated that service quality and safety improvement can be argued as a legitimate interest, provided automated pre-training PII scrubbers and user opt-outs are active.
                  </p>
                </div>
              </div>
            </div>

            {/* Unresolved Questions Panel (§16.2) */}
            <div className="glass-panel p-6 rounded-3xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-bold text-white">Unresolved Questions & Inquiry Backlog (§16.2)</h3>
                </div>
                <span className="text-[10px] font-mono text-slate-400">{unresolvedQuestions.length} Open Inquiries</span>
              </div>
              <div className="space-y-3">
                {unresolvedQuestions.map((uq) => (
                  <div key={uq.id} className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800/40">
                          {uq.id}
                        </span>
                        <span className="text-xs font-semibold text-white">{uq.topic}</span>
                      </div>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {uq.status.replace("_", " ")}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">{uq.question}</p>
                    {uq.linkedBounty && (
                      <div className="pt-1 flex items-center gap-2 text-[11px] text-amber-400">
                        <Gift className="w-3.5 h-3.5" />
                        <Link href="/bounties" className="hover:underline flex items-center gap-1 font-semibold">
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
            <div className="glass-panel p-6 rounded-3xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <span>Linked Prediction Markets (§16.5)</span>
              </h3>
              <div className="space-y-3">
                {markets.map((m) => (
                  <div key={m.market_id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-cyan-400 font-bold">{m.market_id}</span>
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                        {m.state}
                      </span>
                    </div>
                    <p className="text-xs text-slate-200 line-clamp-2">{m.question}</p>
                    <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800">
                      <span className="text-slate-400">Agg Probability:</span>
                      <span className="font-mono font-bold text-cyan-400">
                        {(m.aggregate_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <Link
                href="/markets"
                className="w-full py-2 px-3 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Go to Prediction Markets</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="glass-panel p-6 rounded-3xl space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Gift className="w-4 h-4 text-amber-400" />
                <span>Linked Evidence Bounties (§16.6)</span>
              </h3>
              <div className="space-y-3">
                {bounties.map((b) => (
                  <div key={b.bounty_id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-mono text-amber-400 font-bold">{b.bounty_id}</span>
                      <span className="text-emerald-400 font-bold font-mono">+{b.reward_credits} Credits</span>
                    </div>
                    <p className="text-xs text-slate-200 line-clamp-2">{b.question}</p>
                  </div>
                ))}
              </div>
              <Link
                href="/bounties"
                className="w-full py-2 px-3 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Go to Evidence Bounties</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Argument Graph Shortcut */}
            <div className="glass-panel p-6 rounded-3xl space-y-3">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                <GitFork className="w-4 h-4" />
                <span>Argument Graph (§16.4)</span>
              </div>
              <p className="text-xs text-slate-400">
                Inspect structured dialectic tree connecting statutory evidence, claims, and counter-arguments.
              </p>
              <Link
                href="/graph"
                className="w-full py-2 px-3 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Open Graph Explorer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}

      {activeTab === "facts" && (
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <h3 className="text-sm font-bold text-white">Frozen Case Facts (§14)</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400">Processing Purpose:</span>
              <p className="font-semibold text-slate-100">{currentCase.facts.processing_purpose}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400">Affected Users:</span>
              <p className="font-semibold text-slate-100">{currentCase.facts.affected_users}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400">Consent Mechanism:</span>
              <p className="font-semibold text-slate-100">{currentCase.facts.user_consent_mechanism}</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-400">Retention Period:</span>
              <p className="font-semibold text-slate-100">{currentCase.facts.retention_period_days} Days</p>
            </div>
            <div className="sm:col-span-2 p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <span className="text-slate-400">Data Categories Ingested:</span>
              <div className="flex flex-wrap gap-2">
                {currentCase.facts.data_categories.map((cat, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 text-xs font-mono">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "sources" && (
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <h3 className="text-sm font-bold text-white">Curated Source Collection & Effective Dates (FR-006, FR-007)</h3>
          <div className="space-y-3">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start justify-between gap-4 text-xs">
              <div className="space-y-1">
                <span className="font-mono text-cyan-400 font-bold">gdpr_reg_2016_679</span>
                <h4 className="font-bold text-white">Regulation (EU) 2016/679 (GDPR)</h4>
                <p className="text-slate-400">Article 5(1)(b) Purpose Limitation & Article 6(4) Compatibility Test</p>
              </div>
              <div className="text-right shrink-0">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                  ACTIVE
                </span>
                <p className="text-[10px] text-slate-500 mt-1">Eff: 2018-05-25</p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start justify-between gap-4 text-xs">
              <div className="space-y-1">
                <span className="font-mono text-cyan-400 font-bold">edpb_statement_01_2024</span>
                <h4 className="font-bold text-white">EDPB Statement 01/2024 on Generative AI Model Development</h4>
                <p className="text-slate-400">Paragraph 4: Repurposing support transcripts for LLM fine-tuning</p>
              </div>
              <div className="text-right shrink-0">
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold">
                  ACTIVE
                </span>
                <p className="text-[10px] text-slate-500 mt-1">Eff: 2024-04-17</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "agents" && (
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white">Swarm Agent Activity Summary (§16.2, §16.3)</h3>
              <p className="text-xs text-slate-400">Inspect the specialized autonomous nodes participating in this case investigation.</p>
            </div>
            <Link
              href="/agents"
              className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              <span>Full Agent Lab</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((ag) => (
              <div
                key={ag.agent_id}
                className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase font-bold text-indigo-400">{ag.role}</span>
                  <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    {ag.status}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">{ag.name}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2 mt-1">{ag.current_task}</p>
                </div>
                <div className="flex items-center justify-between text-[11px] pt-2 border-t border-slate-800/80 text-slate-400">
                  <span>Claims: <strong className="text-white font-mono">{ag.claims_generated}</strong></span>
                  <span>Uncertainty: <strong className="text-amber-400 font-mono">{(ag.uncertainty_score * 100).toFixed(0)}%</strong></span>
                  <Link
                    href={`/agents?role=${ag.role}`}
                    className="text-cyan-400 hover:underline flex items-center gap-0.5"
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
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <h3 className="text-sm font-bold text-white">Autonomous Agent Activity Timeline</h3>
          <div className="space-y-4 border-l-2 border-slate-800 pl-4 ml-2">
            {agents.map((ag) => (
              <div key={ag.agent_id} className="relative space-y-1">
                <div className="absolute -left-[23px] top-1.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-950"></div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-white">{ag.name}</span>
                  <span className="text-[10px] font-mono text-slate-400">{ag.elapsed_ms}ms</span>
                </div>
                <p className="text-xs text-slate-300">{ag.current_task}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
