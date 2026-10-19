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
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                §16.3
              </span>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">Agent Laboratory</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Inspect autonomous agent roles, task executions, cited sources, uncertainty estimates, compute cost, and failure diagnostics.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Honest telemetry: static execution snapshot (§16.3)</span>
          </div>
        </div>

        {/* Swarm Resource Consumption Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-0.5">
            <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" /> Active Roles
            </span>
            <div className="text-lg font-bold text-white">{agents.length} Nodes</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-0.5">
            <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
              <Clock className="w-3.5 h-3.5 text-cyan-400" /> Avg Latency
            </span>
            <div className="text-lg font-bold text-white font-mono">{avgLatency} ms</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-0.5">
            <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
              <Zap className="w-3.5 h-3.5 text-amber-400" /> Tokens Ingested
            </span>
            <div className="text-lg font-bold text-white font-mono">{totalTokens}</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-0.5">
            <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
              <DollarSign className="w-3.5 h-3.5 text-emerald-400" /> Execution Cost
            </span>
            <div className="text-lg font-bold text-white font-mono">${totalCost.toFixed(4)}</div>
          </div>
        </div>

        {/* Filters and Failure Toggle */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3">
          <div className="flex flex-wrap items-center gap-2">
            {["ALL", "LEGAL_RESEARCHER", "LEGAL_INTERPRETER", "ADVERSARIAL_RESEARCHER", "EVIDENCE_VERIFIER", "QUANTITATIVE_FORECASTER", "COORDINATOR"].map(
              (role) => (
                <button
                  key={role}
                  onClick={() => setRoleFilter(role)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    roleFilter === role
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-glow"
                      : "text-slate-400 hover:text-white bg-slate-900/60 border border-slate-800"
                  }`}
                >
                  {role.replace(/_/g, " ")}
                </button>
              )
            )}
          </div>

          <button
            onClick={() => setShowFailuresOnly(!showFailuresOnly)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              showFailuresOnly
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-glow-rose"
                : "bg-slate-900/80 text-slate-400 border border-slate-800 hover:text-white"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>Failures Only ({totalFailures})</span>
          </button>
        </div>
      </div>

      {/* Agents Grid */}
      {filteredAgents.length === 0 ? (
        <EmptyState
          icon={<Cpu className="w-7 h-7 text-indigo-400" />}
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
                  className="mt-2 w-full py-1.5 px-3 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Inspect Detailed Stack / Diagnostic Failures</span>
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Failure Diagnostics Modal (§16.3) */}
      {selectedAgentForDiagnostics && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-xl rounded-3xl border border-rose-900/60 bg-slate-950 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                <h3 className="text-base font-bold text-white">Diagnostic Failure Inspector</h3>
              </div>
              <button
                onClick={() => setDiagnosticsAgentId(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-400">
                <span>Agent: <strong className="text-white">{selectedAgentForDiagnostics.name}</strong></span>
                <span className="font-mono text-cyan-400">{selectedAgentForDiagnostics.agent_id}</span>
              </div>
              <div className="text-slate-400">
                Role: <strong className="text-indigo-400 font-mono">{selectedAgentForDiagnostics.role}</strong>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-rose-300 block">Reported Unhandled Diagnostic Logs:</span>
              <div className="p-3 rounded-2xl bg-slate-900 border border-rose-950/80 font-mono text-xs text-rose-200/90 space-y-2 max-h-60 overflow-y-auto">
                {selectedAgentForDiagnostics.failures.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 border-b border-rose-900/30 pb-2 last:border-0 last:pb-0">
                    <span className="text-rose-500 font-bold shrink-0">[{i + 1}]</span>
                    <span>{f}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-1">
              <span className="font-semibold text-slate-300 block">Protocol Handling Policy:</span>
              <p>
                Agent failures do not trigger synthetic retry loops. They are logged immutably, and the coordinator either falls back to deterministic rule evaluations or initiates an Evidence Bounty (§11).
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setDiagnosticsAgentId(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
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
