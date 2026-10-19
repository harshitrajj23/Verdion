"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { ArgumentGraph } from "@/components/ArgumentGraph";
import { GitFork, AlertCircle, ShieldCheck, Download } from "lucide-react";

export default function ArgumentGraphPage() {
  const { graphNodes, graphEdges, currentCase } = useStore();

  const contradictionCount = graphEdges.filter((e) => e.relationship === "CONTRADICTION").length;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                §16.4
              </span>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">Argument Graph Explorer</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Structured network of legal interpretations, supporting statutory evidence, adversarial counter-arguments, and typed relationship edges.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {contradictionCount > 0 && (
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-950/70 text-rose-300 border border-rose-800/40 text-xs font-bold shadow-glow-rose">
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                <span>{contradictionCount} Active Legal Contradictions (FR-022)</span>
              </span>
            )}
          </div>
        </div>

        {/* Quick Meta */}
        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
          <span>Case: <strong className="text-white">{currentCase.id}</strong></span>
          <span>•</span>
          <span>Total Nodes: <strong className="text-cyan-400">{graphNodes.length}</strong></span>
          <span>•</span>
          <span>Directed Edges: <strong className="text-indigo-400">{graphEdges.length}</strong></span>
          <span>•</span>
          <span>Verification Standard: <strong className="text-emerald-400">On-Chain Digest Parity</strong></span>
        </div>
      </div>

      {/* Graph Visualizer & Fallback Table Component */}
      <ArgumentGraph nodes={graphNodes} edges={graphEdges} />
    </div>
  );
}
