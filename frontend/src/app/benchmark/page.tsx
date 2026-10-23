"use client";

import React from "react";
import {
  BarChart3,
  AlertTriangle,
} from "lucide-react";

export default function BenchmarkPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/30">
                §18.1 • §18.2
              </span>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">Empirical Benchmark & Evaluation</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Rigorous comparative testing of VERIDION against 3 baselines across 20 scenarios (14 train / 6 held-out test split).
            </p>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 text-xs text-slate-300 border border-slate-800 font-mono">
            <span>20 Scenarios</span>
          </div>
        </div>

        {/* Hypothesis Testing Notice (PRD §1.2, §2.4) */}
        <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300 leading-relaxed space-y-1">
          <strong className="text-white block">PRD Hypothesis Testing Principle (§1.2, §2.4):</strong>
          <span>
            "A network of agents that must expose evidence, commit to forecasts, accept challenges, and earn rewards under transparent rules can create a more inspectable investigation process than an unaccountable answer from a single model. The project must measure whether bounties improve evidence quality and report actual results honestly."
          </span>
        </div>
      </div>

      {/* Benchmark Status Banner */}
      <div className="glass-panel p-12 rounded-3xl text-center space-y-4 border border-amber-500/30 bg-amber-950/10">
        <div className="inline-flex p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <div className="space-y-2 max-w-md mx-auto">
          <h2 className="text-lg font-bold text-white">Benchmark not yet run on live pipeline.</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Previous metrics were quarantined because they were derived from hardcoded synthetic constants in evaluation stubs. Live pipeline evaluations on the train split have not yet run.
          </p>
        </div>
      </div>
    </div>
  );
}
