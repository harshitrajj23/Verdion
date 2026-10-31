"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { ArgumentGraph } from "@/components/ArgumentGraph";
import { GitFork, AlertCircle, ShieldCheck, Download } from "lucide-react";

export default function ArgumentGraphPage() {
  const { graphNodes, graphEdges, currentCase } = useStore();

  const contradictionCount = graphEdges.filter((e) => e.relationship === "CONTRADICTION").length;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header Card */}
      <div className="apple-card p-6 sm:p-8 rounded-[18px] bg-white border border-hairline shadow-soft space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                §16.4
              </span>
              <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-ink font-display">
                Argument Graph Explorer
              </h1>
            </div>
            <p className="text-[15px] text-muted leading-relaxed">
              Structured network of legal interpretations, supporting statutory evidence, adversarial counter-arguments, and typed relationship edges.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {contradictionCount > 0 && (
              <span className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 text-xs font-semibold shadow-soft">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>{contradictionCount} Active Legal Contradictions (FR-022)</span>
              </span>
            )}
          </div>
        </div>

        {/* Quick Meta Chips */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs text-muted">
          <span className="px-3 py-1 rounded-full bg-cloud border border-hairline text-ink">
            Case: <strong className="font-semibold text-bubblegum-deep">{currentCase.id}</strong>
          </span>
          <span className="px-3 py-1 rounded-full bg-cloud border border-hairline text-ink">
            Total Nodes: <strong className="font-semibold text-bubblegum-deep">{graphNodes.length}</strong>
          </span>
          <span className="px-3 py-1 rounded-full bg-cloud border border-hairline text-ink">
            Directed Edges: <strong className="font-semibold text-bubblegum-deep">{graphEdges.length}</strong>
          </span>
          <span className="px-3 py-1 rounded-full bg-cloud border border-hairline text-ink">
            Verification: <strong className="font-semibold text-emerald-700">On-Chain Digest Parity</strong>
          </span>
        </div>
      </div>

      {/* Graph Visualizer & Fallback Table Component */}
      <ArgumentGraph nodes={graphNodes} edges={graphEdges} />
    </div>
  );
}
