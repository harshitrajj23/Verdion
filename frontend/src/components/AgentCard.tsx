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
    ACTIVE: "bg-lavender-100 text-lavender-800 border-lavender-200",
    COMPLETED: "bg-lavender-50 text-lavender-700 border-lavender-200",
    FAILED: "bg-rose-50 text-rose-700 border-rose-200",
    IDLE: "bg-cream-200 text-ink-muted border-cream-300",
    ABSTAINED: "bg-amber-50 text-amber-800 border-amber-200"
  }[agent.status];

  return (
    <div className="apple-card space-y-4 hover:border-lavender-300/90 transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-cream-200 pb-3">
        <div>
          <span className="text-[10px] font-mono text-lavender-700 tracking-wider uppercase font-semibold">
            {agent.role}
          </span>
          <h3 className="text-base font-semibold text-ink mt-0.5 font-appleDisplay">{agent.name}</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${statusColor}`}>
          {agent.status}
        </span>
      </div>

      {/* Current Task */}
      <div className="space-y-1">
        <span className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider">Current Task:</span>
        <p className="text-xs text-ink bg-cream-50 p-3 rounded-[12px] border border-cream-200 leading-relaxed">
          {agent.current_task}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2.5 rounded-[12px] bg-cream-50 border border-cream-200">
          <span className="text-[10px] text-ink-muted block font-medium">Sources</span>
          <span className="text-xs font-mono font-bold text-lavender-700">{agent.sources_consulted}</span>
        </div>
        <div className="p-2.5 rounded-[12px] bg-cream-50 border border-cream-200">
          <span className="text-[10px] text-ink-muted block font-medium">Claims</span>
          <span className="text-xs font-mono font-bold text-ink">{agent.claims_generated}</span>
        </div>
        <div className="p-2.5 rounded-[12px] bg-cream-50 border border-cream-200">
          <span className="text-[10px] text-ink-muted block font-medium">Objections</span>
          <span className="text-xs font-mono font-bold text-rose-700">{agent.counterarguments_count}</span>
        </div>
      </div>

      {/* Diagnostic & Cost Metrics (§16.3) */}
      <div className="pt-2 border-t border-cream-200 space-y-2 text-[11px]">
        <div className="flex items-center justify-between text-ink-secondary">
          <span className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-ink-muted" /> Latency:
          </span>
          <span className="font-mono text-ink font-medium">{agent.elapsed_ms} ms</span>
        </div>
        <div className="flex items-center justify-between text-ink-secondary">
          <span className="flex items-center gap-1.5">
            <Coins className="w-3.5 h-3.5 text-ink-muted" /> Compute Cost:
          </span>
          <span className="font-mono text-ink font-medium">
            ${agent.cost_usd.toFixed(4)} ({agent.token_usage} tokens)
          </span>
        </div>
        <div className="flex items-center justify-between text-ink-secondary">
          <span className="flex items-center gap-1.5">
            <HelpCircle className="w-3.5 h-3.5 text-ink-muted" /> Uncertainty:
          </span>
          <span className="font-mono font-semibold text-amber-800">
            {(agent.uncertainty_score * 100).toFixed(0)}%
          </span>
        </div>
        {agent.forecast_prob !== undefined && (
          <div className="flex items-center justify-between text-ink-secondary">
            <span>Forecast Probability:</span>
            <span className="font-mono font-bold text-lavender-700">
              {(agent.forecast_prob * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {/* Failure Log (§16.3) */}
      {agent.failures.length > 0 ? (
        <div className="p-2.5 rounded-[12px] bg-rose-50 border border-rose-200 text-[11px] text-rose-800 flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Recorded Diagnostic Failures:</span>
            {agent.failures.map((f, i) => (
              <p key={i}>{f}</p>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-[11px] text-ink-muted flex items-center gap-1.5 pt-1">
          <CheckCircle2 className="w-3.5 h-3.5 text-lavender-600" />
          <span>Zero uncaught diagnostic failures</span>
        </div>
      )}

      {/* Last Output Summary */}
      <div className="text-[11px] text-ink-secondary italic bg-cream-100 p-2.5 rounded-[10px] border border-cream-200 leading-relaxed">
        "{agent.last_output_summary}"
      </div>
    </div>
  );
};

