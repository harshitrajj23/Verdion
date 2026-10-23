"use client";

import React, { useMemo, useState, useEffect } from "react";
import {
  BarChart3,
  AlertTriangle,
  Info,
  CheckCircle2,
  Terminal,
  Cpu,
  GitCommit,
  Clock,
  Layers,
  ShieldAlert,
  Flame,
} from "lucide-react";
import rawBenchmarkJson from "@/data/results_train_live.json";
import {
  validateBenchmarkData,
  computeDynamicallyComputedMeans,
  LiveBenchmarkData,
} from "@/lib/benchmarkData";

export default function BenchmarkPage() {
  const [dataResult, setDataResult] = useState<LiveBenchmarkData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    // Validate live train benchmark data on mount
    const res = validateBenchmarkData(rawBenchmarkJson);
    if (!res.success) {
      setLoadError(res.error);
    } else {
      setDataResult(res.data);
    }
  }, []);

  // Compute aggregate means dynamically from the loaded scenario array
  const computedMeans = useMemo(() => {
    if (!dataResult) return null;
    return computeDynamicallyComputedMeans(dataResult.per_scenario);
  }, [dataResult]);

  if (loadError) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-500/30 text-rose-300 space-y-3">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-400" />
            <h2 className="text-lg font-bold text-white">Benchmark Data Validation Error</h2>
          </div>
          <p className="text-sm font-mono text-rose-200">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!dataResult || !computedMeans) {
    return (
      <div className="p-12 text-center text-slate-400 font-mono text-sm animate-pulse">
        Loading live train benchmark results...
      </div>
    );
  }

  const { metadata, stability_summary, per_scenario } = dataResult;

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-7xl mx-auto pb-16">
      {/* Title & Strict Scope Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4 border border-purple-500/20 bg-slate-900/40">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/30">
                §18.1 • §18.2 Live Evaluation
              </span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">
                In-Sample Train Split
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Train split, 14 scenarios, in-sample. Not a generalization.
            </h1>
            <p className="text-xs text-slate-400">
              Deterministic evaluation executed against local Ollama (<span className="text-slate-300 font-mono">{metadata.model_name}</span>) with zero external API calls.
            </p>
          </div>

          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 flex items-center gap-2">
              <GitCommit className="w-3.5 h-3.5 text-purple-400" />
              <span>{metadata.git_commit_hash.slice(0, 7)}</span>
            </div>
            <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-emerald-400 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5" />
              <span>Ollama v{metadata.ollama_version} ({metadata.quantization || "Q4_K_M"})</span>
            </div>
          </div>
        </div>

        {/* Prominent Notice: Held-Out & Relevance Status */}
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="text-amber-100 font-bold block text-sm">
              Held-out evaluation has not been run. Relevance labels have not been completed.
            </strong>
            <p className="text-amber-200/90 leading-relaxed">
              The 6 held-out test scenarios (<span className="font-mono">scen_15</span>–<span className="font-mono">scen_20</span>) have NOT been evaluated to prevent benchmark contamination. All metrics below represent solely the 14 training scenarios evaluated in-sample. <em>Held-out not run.</em>
            </p>
          </div>
        </div>

        {/* Critical Caveats Panel */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          {/* Caveat 1: Deterministic Greedy Decoding */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-xs">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold">
              <Clock className="w-4 h-4" />
              <span>Decoding Stability</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Labeled as <strong>“deterministic for fixed inputs and software at temperature 0”</strong> (per-scenario spread 0.0000 across 3 consecutive runs). Forecaster output is sensitive to upstream context variations.
            </p>
          </div>

          {/* Caveat 2: Placeholder Evidence Digest */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-xs">
            <div className="flex items-center gap-2 text-rose-400 font-semibold">
              <ShieldAlert className="w-4 h-4" />
              <span>Placeholder Evidence Digest</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              The evidence digest passed into the live prompt was <span className="font-mono text-slate-300">0x0000000000000000</span> (placeholder), not a canonical digest computed via <span className="font-mono text-slate-300">compute_evidence_digest</span>.
            </p>
          </div>

          {/* Caveat 3: Event Definition Mismatch */}
          <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-1.5 text-xs">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold">
              <Layers className="w-4 h-4" />
              <span>Event-Definition Mismatch</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Forecaster prompt defines resolution as general <em>compliance violation or legal liability</em>, whereas <span className="font-mono text-slate-300">PredictionMarket</span> resolves on <em>specific evaluator rubric gaps</em>. Definitions must harmonize before contract market integration.
            </p>
          </div>
        </div>

        {/* Upstream Contradiction Caveat */}
        <div className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-xs text-slate-400 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
          <span>
            <strong>Upstream Signal Contradictions:</strong> In scenarios like <span className="font-mono text-slate-300">scen_09</span>, upstream claims contain unadjudicated contradictions across sub-rules (e.g. storage limitation compliance alongside unlawful third-party model transfer without DPA), which the Forecaster synthesizes without prior resolution.
          </span>
        </div>
      </div>

      {/* Aggregate Mean Brier Cards (Dynamically Computed) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider font-mono">
            Aggregate Performance (Dynamically Computed from Loaded JSON)
          </h2>
          <span className="text-xs font-mono text-slate-400">Mean Brier Score: Lower is better (0.0 = perfect calibration)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Baseline 1: Constant 0.65 */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 bg-slate-900/30 space-y-2">
            <div className="text-xs font-mono text-slate-400">Baseline 1 (Constant 0.65)</div>
            <div className="text-2xl font-black text-slate-200 font-mono">
              {computedMeans.mean_constant.toFixed(4)}
            </div>
            <p className="text-xs text-slate-400">
              Heuristic prior assigning fixed p = 0.65 across all 14 scenarios.
            </p>
          </div>

          {/* Baseline 2: Train Base Rate */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 bg-slate-900/30 space-y-2">
            <div className="text-xs font-mono text-slate-400">
              Baseline 2 (Train Base Rate: 8/14 = {metadata.train_base_rate})
            </div>
            <div className="text-2xl font-black text-slate-200 font-mono">
              {computedMeans.mean_base.toFixed(4)}
            </div>
            <p className="text-xs text-slate-400">
              In-sample train base-rate baseline assigning p = 0.5714 to all scenarios.
            </p>
          </div>

          {/* Live Pipeline: Forecaster */}
          <div className="glass-panel p-5 rounded-2xl border border-purple-500/30 bg-purple-950/10 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-purple-400 font-semibold">
              <span>Live Pipeline Forecaster</span>
              <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 text-[10px]">
                In-Sample Train
              </span>
            </div>
            <div className="text-2xl font-black text-purple-300 font-mono">
              {computedMeans.mean_live.toFixed(4)}
            </div>
            <p className="text-xs text-slate-400">
              Full swarm (Researcher → Interpreter → Adversarial → Forecaster) running on local Ollama.
            </p>
          </div>
        </div>
      </div>

      {/* Stability Summary Panel */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 bg-slate-900/20 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <div>
            <span className="text-white font-bold">Decoding Stability Check:</span>{" "}
            <span className="text-emerald-400 font-bold">{stability_summary.verdict}</span> (Threshold spread ≤ {stability_summary.threshold})
          </div>
        </div>
        <div className="flex items-center gap-6 text-slate-400">
          <div>Scenarios Tested: <strong className="text-white">{stability_summary.total_scenarios}</strong></div>
          <div>Unstable Count: <strong className="text-emerald-400">{stability_summary.unstable_count}</strong></div>
          <div>Mode: <span className="text-slate-300">Deterministic decoding for fixed inputs and software</span></div>
        </div>
      </div>

      {/* Detailed Per-Scenario Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider font-mono">
            Train Split Per-Scenario Results ({per_scenario.length} Scenarios)
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Ground Truth: 1 = Compliance Violation / Liability, 0 = Compliant
          </span>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/60">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400">
                <th className="p-3.5 font-semibold">Scenario ID</th>
                <th className="p-3.5 font-semibold">Title</th>
                <th className="p-3.5 font-semibold text-center">Label (y)</th>
                <th className="p-3.5 font-semibold text-right">Const 0.65 (p / Brier)</th>
                <th className="p-3.5 font-semibold text-right">Base Rate (p / Brier)</th>
                <th className="p-3.5 font-semibold text-right">Forecaster (p / Brier)</th>
                <th className="p-3.5 font-semibold text-center">3 Runs (Spread)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {per_scenario.map((s) => {
                const isPositive = s.ground_truth_label === 1;
                return (
                  <tr key={s.scenario_id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-3.5 font-bold text-purple-300 whitespace-nowrap">
                      {s.scenario_id}
                    </td>
                    <td className="p-3.5 text-slate-300 max-w-xs truncate" title={s.title}>
                      {s.title}
                    </td>
                    <td className="p-3.5 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${
                          isPositive
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                            : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        }`}
                      >
                        {s.ground_truth_label}
                      </span>
                    </td>
                    <td className="p-3.5 text-right text-slate-400">
                      <span>{s.constant_0_65.probability.toFixed(2)}</span> /{" "}
                      <span className="text-slate-300 font-semibold">{s.constant_0_65.brier.toFixed(4)}</span>
                    </td>
                    <td className="p-3.5 text-right text-slate-400">
                      <span>{s.base_rate.probability.toFixed(4)}</span> /{" "}
                      <span className="text-slate-300 font-semibold">{s.base_rate.brier.toFixed(4)}</span>
                    </td>
                    <td className="p-3.5 text-right">
                      <span className="text-purple-300 font-bold">{s.live_forecaster.probability.toFixed(2)}</span> /{" "}
                      <span className="text-emerald-400 font-bold">{s.live_forecaster.brier.toFixed(4)}</span>
                    </td>
                    <td className="p-3.5 text-center text-slate-400 whitespace-nowrap">
                      <span>[{s.stability_check.runs.join(", ")}]</span>{" "}
                      <span className="text-emerald-400 font-bold">({s.stability_check.spread.toFixed(4)})</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
