"use client";

import React from "react";
import { AgentMetric } from "@/lib/mockData";
import {
  Clock,
  Database,
  Coins,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  FileText,
  Activity,
  ShieldAlert
} from "lucide-react";

interface AgentCardProps {
  agent: AgentMetric;
}

export const AgentCard: React.FC<AgentCardProps> = ({ agent }) => {
  const statusColor = {
    ACTIVE: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    COMPLETED: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    FAILED: "bg-rose-500/10 text-rose-400 border-rose-500/30",
    IDLE: "bg-slate-800 text-slate-400 border-slate-700",
    ABSTAINED: "bg-amber-500/10 text-amber-400 border-amber-500/30"
  }[agent.status];

  return (
    <div className="glass-panel p-5 rounded-2xl space-y-4 glass-panel-hover">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-800/80 pb-3">
        <div>
          <span className="text-[10px] font-mono text-slate-400 tracking-wider uppercase">
            {agent.role}
          </span>
          <h3 className="text-base font-bold text-white mt-0.5">{agent.name}</h3>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${statusColor}`}>
          {agent.status}
        </span>
      </div>

      {/* Current Task */}
      <div className="space-y-1">
        <span className="text-[11px] font-semibold text-slate-400">Current Task:</span>
        <p className="text-xs text-slate-200 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/80 leading-relaxed">
          {agent.current_task}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 block">Sources</span>
          <span className="text-xs font-mono font-bold text-emerald-400">{agent.sources_consulted}</span>
        </div>
        <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 block">Claims</span>
          <span className="text-xs font-mono font-bold text-cyan-400">{agent.claims_generated}</span>
        </div>
        <div className="p-2 rounded-xl bg-slate-900/60 border border-slate-800/60">
          <span className="text-[10px] text-slate-400 block">Objections</span>
          <span className="text-xs font-mono font-bold text-rose-400">{agent.counterarguments_count}</span>
        </div>
      </div>

      {/* Diagnostic & Cost Metrics (§16.3) */}
      <div className="pt-2 border-t border-slate-800/80 space-y-2 text-[11px]">
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-500" /> Latency:
          </span>
          <span className="font-mono text-slate-300">{agent.elapsed_ms} ms</span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <Coins className="w-3.5 h-3.5 text-slate-500" /> Compute Cost:
          </span>
          <span className="font-mono text-slate-300">
            ${agent.cost_usd.toFixed(4)} ({agent.token_usage} tokens)
          </span>
        </div>
        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-slate-500" /> Uncertainty:
          </span>
          <span className="font-mono font-semibold text-amber-400">
            {(agent.uncertainty_score * 100).toFixed(0)}%
          </span>
        </div>
        {agent.forecast_prob !== undefined && (
          <div className="flex items-center justify-between text-slate-400">
            <span>Forecast Probability:</span>
            <span className="font-mono font-bold text-cyan-400">
              {(agent.forecast_prob * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Failure Log (§16.3) */}
      {agent.failures.length > 0 ? (
        <div className="p-2.5 rounded-xl bg-rose-950/40 border border-rose-800/40 text-[11px] text-rose-300 flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Recorded Diagnostic Failures:</span>
            {agent.failures.map((f, i) => (
              <p key={i}>{f}</p>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-[10px] text-slate-500 flex items-center gap-1.5 pt-1">
          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
          <span>Zero uncaught diagnostic failures</span>
        </div>
      )}

      {/* Last Output Summary */}
      <div className="text-[11px] text-slate-400 italic bg-slate-950/40 p-2 rounded-lg border border-slate-900">
        "{agent.last_output_summary}"
      </div>
    </div>
  );
};
