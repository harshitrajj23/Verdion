"use client";

import React, { useState } from "react";
import { useStore } from "@/lib/store";
import { AgentCard } from "@/components/AgentCard";
import { EmptyState } from "@/components/EmptyState";
import {
  Cpu,
  ShieldCheck,
  Zap,
  DollarSign,
  Clock,
  Layers,
  AlertTriangle,
  X,
  FileCode,
  ShieldAlert
} from "lucide-react";

export default function AgentLaboratoryPage() {
  const { agents } = useStore();
  const [roleFilter, setRoleFilter] = useState<string>("ALL");
  const [showFailuresOnly, setShowFailuresOnly] = useState<boolean>(false);
  const [diagnosticsAgentId, setDiagnosticsAgentId] = useState<string | null>(null);

  const filteredAgents = agents.filter((a) => {
    const matchesRole = roleFilter === "ALL" || a.role === roleFilter;
    const matchesFailures = !showFailuresOnly || a.failures.length > 0;
    return matchesRole && matchesFailures;
  });

  const totalTokens = agents.reduce((acc, a) => acc + a.token_usage, 0);
  const totalCost = agents.reduce((acc, a) => acc + a.cost_usd, 0);
  const avgLatency = Math.round(agents.reduce((acc, a) => acc + a.elapsed_ms, 0) / (agents.length || 1));
  const totalFailures = agents.reduce((acc, a) => acc + a.failures.length, 0);

  const selectedAgentForDiagnostics = agents.find((a) => a.agent_id === diagnosticsAgentId);

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* ── Apple Header Card ── */}
      <div className="apple-card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200">
                §16.3
              </span>
              <h1 className="text-2xl sm:text-3xl font-semibold text-ink tracking-tight font-appleDisplay">
                Agent Laboratory
              </h1>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              Inspect autonomous agent roles, task executions, cited sources, uncertainty estimates, compute cost, and failure diagnostics.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-ink-secondary bg-cream-50 px-3.5 py-1.5 rounded-full border border-cream-300">
            <ShieldCheck className="w-4 h-4 text-lavender-600" />
            <span>Honest telemetry: static execution snapshot (§16.3)</span>
          </div>
        </div>

        {/* Swarm Resource Consumption Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300 space-y-0.5">
            <span className="text-[10px] text-ink-muted flex items-center gap-1 font-semibold uppercase tracking-wider">
              <Cpu className="w-3.5 h-3.5 text-lavender-600" /> Active Roles
            </span>
            <div className="text-xl font-semibold text-ink font-appleDisplay">{agents.length} Nodes</div>
          </div>

          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300 space-y-0.5">
            <span className="text-[10px] text-ink-muted flex items-center gap-1 font-semibold uppercase tracking-wider">
              <Clock className="w-3.5 h-3.5 text-lavender-600" /> Avg Latency
            </span>
            <div className="text-xl font-semibold text-ink font-mono">{avgLatency} ms</div>
          </div>

          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300 space-y-0.5">
            <span className="text-[10px] text-ink-muted flex items-center gap-1 font-semibold uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5 text-lavender-600" /> Tokens Ingested
            </span>
            <div className="text-xl font-semibold text-ink font-mono">{totalTokens}</div>
          </div>

          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300 space-y-0.5">
            <span className="text-[10px] text-ink-muted flex items-center gap-1 font-semibold uppercase tracking-wider">
              <DollarSign className="w-3.5 h-3.5 text-lavender-600" /> Execution Cost
            </span>
            <div className="text-xl font-semibold text-ink font-mono">${totalCost.toFixed(4)}</div>
          </div>
        </div>

        {/* Filters and Failure Toggle: Pill Groups */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="inline-flex p-1 rounded-full bg-cloud border border-hairline max-w-full overflow-x-auto scrollbar-none">
            {["ALL", "LEGAL_RESEARCHER", "LEGAL_INTERPRETER", "ADVERSARIAL_RESEARCHER", "EVIDENCE_VERIFIER", "QUANTITATIVE_FORECASTER", "COORDINATOR"].map(
              (role) => (
                <button
                  key={role}
                  onClick={() => setRoleFilter(role)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-150 active:scale-[0.97] whitespace-nowrap ${
                    roleFilter === role
                      ? "bg-bubblegum text-white shadow-soft font-semibold"
                      : "text-muted hover:text-ink hover:bg-bubblegum-soft/40"
                  }`}
                >
                  {role.replace(/_/g, " ")}
                </button>
              )
            )}
          </div>

          <button
            onClick={() => setShowFailuresOnly(!showFailuresOnly)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 transition-all duration-150 active:scale-[0.97] ${
              showFailuresOnly
                ? "bg-rose-100 text-rose-800 border border-rose-300 shadow-soft"
                : "bg-cloud text-muted border border-hairline hover:text-ink"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            <span>Failures Only ({totalFailures})</span>
          </button>
        </div>
      </div>

      {/* Agents Grid */}
      {filteredAgents.length === 0 ? (
        <EmptyState
          icon={<Cpu className="w-7 h-7 text-lavender-600" />}
          title="No Agents Match Filter"
          description={`No agent telemetry matching the selected role '${roleFilter}'.`}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <div key={agent.agent_id} className="relative">
              <AgentCard agent={agent} />
              {agent.failures.length > 0 && (
                <button
                  onClick={() => setDiagnosticsAgentId(agent.agent_id)}
                  className="mt-2 w-full py-2 px-3 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors active:scale-[0.97]"
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                  <span>Inspect Detailed Stack / Diagnostics</span>
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Failure Diagnostics Modal */}
      {selectedAgentForDiagnostics && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-md animate-fade-in-up">
          <div className="relative w-full max-w-xl rounded-[20px] border border-cream-300 bg-white p-6 sm:p-8 shadow-apple-hover space-y-4">
            <div className="flex items-center justify-between border-b border-cream-200 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-600" />
                <h3 className="text-base font-semibold text-ink font-appleDisplay">Diagnostic Failure Inspector</h3>
              </div>
              <button
                onClick={() => setDiagnosticsAgentId(null)}
                className="text-ink-muted hover:text-ink p-1 rounded-full hover:bg-cream-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-ink-secondary">
                <span>Agent: <strong className="text-ink">{selectedAgentForDiagnostics.name}</strong></span>
                <span className="font-mono text-lavender-700 font-semibold">{selectedAgentForDiagnostics.agent_id}</span>
              </div>
              <div className="text-ink-secondary">
                Role: <strong className="text-lavender-700 font-mono">{selectedAgentForDiagnostics.role}</strong>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-rose-800 block">Reported Unhandled Diagnostic Logs:</span>
              <div className="p-3.5 rounded-[14px] bg-rose-50 border border-rose-200 font-mono text-xs text-rose-950 space-y-2 max-h-60 overflow-y-auto">
                {selectedAgentForDiagnostics.failures.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 border-b border-rose-200/60 pb-2 last:border-0 last:pb-0">
                    <span className="text-rose-600 font-bold shrink-0">[{i + 1}]</span>
                    <span>{f}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 text-xs text-ink-secondary space-y-1">
              <span className="font-semibold text-ink block">Protocol Handling Policy:</span>
              <p>
                Agent failures do not trigger synthetic retry loops. They are logged immutably, and the coordinator either falls back to deterministic rule evaluations or initiates an Evidence Bounty (§11).
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setDiagnosticsAgentId(null)}
                className="apple-btn-secondary text-xs px-4 py-2"
              >
                Dismiss Diagnostics
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

