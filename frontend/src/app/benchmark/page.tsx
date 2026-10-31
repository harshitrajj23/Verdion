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
  computeDiscriminationAndBootstrap,
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

  // Compute separation and bootstrap CI dynamically
  const discriminationMetrics = useMemo(() => {
    if (!dataResult) return null;
    return computeDiscriminationAndBootstrap(dataResult.per_scenario);
  }, [dataResult]);

  if (loadError) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <div className="p-6 rounded-[18px] bg-rose-50 border border-rose-200 text-rose-800 space-y-3">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-rose-600" />
            <h2 className="text-lg font-bold text-rose-900">Benchmark Data Validation Error</h2>
          </div>
          <p className="text-sm font-mono text-rose-700">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!dataResult || !computedMeans) {
    return (
      <div className="p-12 text-center text-ink-secondary font-mono text-sm animate-pulse">
        Loading live train benchmark results...
      </div>
    );
  }

  const { metadata, stability_summary, per_scenario } = dataResult;

  return (
    <div className="space-y-8 animate-fade-in-up max-w-7xl mx-auto pb-16">
      {/* Title & Strict Scope Banner */}
      <div className="apple-card p-6 sm:p-8 rounded-[18px] bg-white border border-hairline shadow-soft space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-hairline pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                §18.1 • §18.2 Live Evaluation
              </span>
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft/60 text-bubblegum-deep border border-hairline">
                In-Sample Train Split
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink font-display">
              Train split, 14 scenarios, in-sample. Not a generalization.
            </h1>
            <p className="text-[15px] text-muted leading-relaxed">
              Deterministic evaluation executed against local Ollama (<span className="text-ink font-mono font-medium">{metadata.model_name}</span>) with zero external API calls.
            </p>
          </div>

          <div className="flex items-center gap-2.5 font-mono text-xs">
            <div className="px-3.5 py-1.5 rounded-full bg-cloud border border-hairline text-ink flex items-center gap-2 shadow-soft">
              <GitCommit className="w-3.5 h-3.5 text-bubblegum" />
              <span>{metadata.git_commit_hash.slice(0, 7)}</span>
            </div>
            <div className="px-3.5 py-1.5 rounded-full bg-cloud border border-hairline text-emerald-700 flex items-center gap-2 shadow-soft">
              <Cpu className="w-3.5 h-3.5" />
              <span>Ollama v{metadata.ollama_version} ({metadata.quantization || "Q4_K_M"})</span>
            </div>
          </div>
        </div>

        {/* Prominent Notice: Held-Out & Relevance Status */}
        <div className="p-4 rounded-[16px] bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="text-amber-950 font-bold block text-sm">
              Held-out evaluation has not been run. Relevance labels have not been completed.
            </strong>
            <p className="text-amber-900/90 leading-relaxed">
              The 6 held-out test scenarios (<span className="font-mono">scen_15</span>–<span className="font-mono">scen_20</span>) have NOT been evaluated to prevent benchmark contamination. All metrics below represent solely the 14 training scenarios evaluated in-sample. <em>Held-out not run.</em>
            </p>
          </div>
        </div>

        {/* Current Limitations Panel */}
        <div className="space-y-2.5 pt-2">
          <div className="text-xs font-mono font-bold text-bubblegum-deep uppercase tracking-wider flex items-center gap-2 font-display">
            <AlertTriangle className="w-4 h-4 text-bubblegum" />
            <span>Current Architectural Limitations (Unfinished Prototype Notice)</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Limitation 1: Deterministic Greedy Decoding */}
            <div className="p-4 rounded-[16px] bg-cloud border border-hairline space-y-1.5 text-xs">
              <div className="flex items-center gap-2 text-bubblegum-deep font-semibold font-display">
                <Clock className="w-4 h-4 text-bubblegum" />
                <span>Limitation 1: Decoding Sensitivity</span>
              </div>
              <p className="text-muted leading-relaxed">
                Labeled as <strong>“deterministic for fixed inputs and software at temperature 0”</strong> (per-scenario spread 0.0000 across 3 consecutive runs). Forecaster output is sensitive to upstream context variations and does not reflect robustness across prompts or runtime environments.
              </p>
            </div>

            {/* Limitation 2: Placeholder Evidence Digest */}
            <div className="p-4 rounded-[16px] bg-cloud border border-hairline space-y-1.5 text-xs">
              <div className="flex items-center gap-2 text-rose-700 font-semibold font-display">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <span>Limitation 2: Placeholder Digest</span>
              </div>
              <p className="text-muted leading-relaxed">
                The evidence digest passed into the live prompt was <span className="font-mono text-ink">0x0000000000000000</span> (a zero-bytes stub), not a canonical digest computed via <span className="font-mono text-ink">compute_evidence_digest</span>. Stored scores were not evaluated against real cryptographically linked digests.
              </p>
            </div>

            {/* Limitation 3: Event Definition Mismatch */}
            <div className="p-4 rounded-[16px] bg-cloud border border-hairline space-y-1.5 text-xs">
              <div className="flex items-center gap-2 text-bubblegum-deep font-semibold font-display">
                <Layers className="w-4 h-4 text-bubblegum" />
                <span>Limitation 3: Event-Definition Mismatch</span>
              </div>
              <p className="text-muted leading-relaxed">
                Forecaster prompt defines resolution as general <em>compliance violation or legal liability</em>, whereas <span className="font-mono text-ink">PredictionMarket</span> contract resolves on <em>specific evaluator rubric gaps</em>. Definitions must match before any market can consume these probabilities.
              </p>
            </div>
          </div>
        </div>

        {/* Upstream Contradiction Caveat */}
        <div className="p-3.5 rounded-[14px] bg-cloud border border-hairline text-xs text-muted flex items-start gap-2.5">
          <Info className="w-4 h-4 text-bubblegum shrink-0 mt-0.5" />
          <span className="leading-relaxed">
            <strong className="text-ink">Limitation 4: Unadjudicated Upstream Contradictions:</strong> In scenarios like <span className="font-mono text-ink font-semibold">scen_09</span>, upstream claims contain unadjudicated contradictions across sub-rules (e.g. storage limitation compliance alongside unlawful third-party model transfer without DPA), which the Forecaster synthesizes without prior resolution.
          </span>
        </div>
      </div>

      {/* Aggregate Mean Brier Cards (Dynamically Computed) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-muted uppercase tracking-widest font-mono">
            Aggregate Performance (Dynamically Computed from Loaded JSON)
          </h2>
          <span className="text-xs font-mono text-muted">Mean Brier Score: Lower is better (0.0 = perfect calibration)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Baseline 1: Constant 0.65 */}
          <div className="apple-card p-5 rounded-[18px] bg-white border border-hairline shadow-soft space-y-2">
            <div className="text-xs font-mono text-muted">Baseline 1 (Constant 0.65)</div>
            <div className="text-3xl font-extrabold text-ink font-mono">
              {computedMeans.mean_constant.toFixed(4)}
            </div>
            <p className="text-xs text-muted leading-relaxed">
              Heuristic prior assigning fixed p = 0.65 across all 14 scenarios.
            </p>
          </div>

          {/* Baseline 2: Train Base Rate */}
          <div className="apple-card p-5 rounded-[18px] bg-white border border-hairline shadow-soft space-y-2">
            <div className="text-xs font-mono text-muted">
              Baseline 2 (Train Base Rate: 8/14 = {metadata.train_base_rate})
            </div>
            <div className="text-3xl font-extrabold text-ink font-mono">
              {computedMeans.mean_base.toFixed(4)}
            </div>
            <p className="text-xs text-muted leading-relaxed">
              In-sample train base-rate baseline assigning p = 0.5714 to all scenarios.
            </p>
          </div>

          {/* Live Pipeline: Forecaster */}
          <div className="apple-card p-5 rounded-[18px] bg-bubblegum-soft/30 border border-hairline shadow-soft space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-bubblegum-deep font-semibold">
              <span className="font-display">Live Pipeline Forecaster</span>
              <span className="px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline text-[10px]">
                In-Sample Train
              </span>
            </div>
            <div className="text-3xl font-extrabold text-bubblegum-deep font-mono">
              {computedMeans.mean_live.toFixed(4)}
            </div>
            <p className="text-xs text-amber-800 font-medium leading-relaxed">
              ⚠️ Unvalidated in-sample figure: Subject to placeholder digest, upstream contradictions, and event mismatch. Not a validated forecaster.
            </p>
          </div>
        </div>
      </div>

      {/* Discrimination & Calibration Metrics (In-Sample, Train Only) */}
      {discriminationMetrics && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-muted uppercase tracking-widest font-mono">
              Discrimination & Calibration Metrics
            </h2>
            <span className="text-xs font-mono text-muted">Strictly in-sample, train only. Zero forecasting skill claimed.</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="apple-card p-5 rounded-[18px] bg-white border border-hairline shadow-soft space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-muted font-semibold">Class Separation [mean p(1) - mean p(0)]</span>
                <span className="px-2.5 py-0.5 rounded-full bg-cloud text-muted text-[10px] font-mono border border-hairline">in-sample, train only</span>
              </div>
              <div className="text-3xl font-extrabold text-ink font-mono">
                +{discriminationMetrics.separation.toFixed(4)}
              </div>
              <p className="text-xs text-muted leading-relaxed">
                Mean forecast on positives ({discriminationMetrics.mean_p_pos.toFixed(4)}) minus negatives ({discriminationMetrics.mean_p_neg.toFixed(4)}). In-sample train separation, not out-of-sample skill.
              </p>
            </div>

            <div className="apple-card p-5 rounded-[18px] bg-white border border-hairline shadow-soft space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-muted font-semibold">Bootstrap 95% CI (Forecaster - Base Rate)</span>
                <span className="px-2.5 py-0.5 rounded-full bg-cloud text-muted text-[10px] font-mono border border-hairline">in-sample, train only</span>
              </div>
              <div className="text-3xl font-extrabold text-ink font-mono">
                [{discriminationMetrics.ci_lower.toFixed(4)}, {discriminationMetrics.ci_upper.toFixed(4)}]
              </div>
              <p className="text-xs text-muted leading-relaxed">
                10,000 bootstrap resamples. Interval {discriminationMetrics.includes_zero ? "includes zero (no statistically significant edge over base rate)" : "excludes zero"}, confirming no claimed forecasting skill.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Stability Summary Panel */}
      <div className="p-4 sm:p-5 rounded-[16px] bg-cloud border border-hairline flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <div>
            <span className="text-ink font-bold">Decoding Stability Check:</span>{" "}
            <span className="text-emerald-700 font-bold">{stability_summary.verdict}</span> (Threshold spread ≤ {stability_summary.threshold})
          </div>
        </div>
        <div className="flex items-center gap-6 text-muted">
          <div>Scenarios Tested: <strong className="text-ink font-semibold">{stability_summary.total_scenarios}</strong></div>
          <div>Unstable Count: <strong className="text-emerald-700 font-semibold">{stability_summary.unstable_count}</strong></div>
          <div>Mode: <span className="text-ink font-medium">Deterministic decoding for fixed inputs and software</span></div>
        </div>
      </div>

      {/* Detailed Per-Scenario Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-muted uppercase tracking-widest font-mono">
            Train Split Per-Scenario Results ({per_scenario.length} Scenarios)
          </h2>
          <span className="text-xs text-muted font-mono">
            Ground Truth: 1 = Compliance Violation / Liability, 0 = Compliant
          </span>
        </div>

        <div className="overflow-x-auto rounded-[18px] border border-hairline bg-white shadow-soft">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-hairline bg-cloud text-muted">
                <th className="p-3.5 font-semibold">Scenario ID</th>
                <th className="p-3.5 font-semibold">Title</th>
                <th className="p-3.5 font-semibold text-center">Label (y)</th>
                <th className="p-3.5 font-semibold text-right">Const 0.65 (p / Brier)</th>
                <th className="p-3.5 font-semibold text-right">Base Rate (p / Brier)</th>
                <th className="p-3.5 font-semibold text-right">Forecaster (p / Brier)</th>
                <th className="p-3.5 font-semibold text-center">3 Runs (Spread)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {per_scenario.map((s) => {
                const isPositive = s.ground_truth_label === 1;
                return (
                  <tr key={s.scenario_id} className="hover:bg-cloud/60 transition-colors">
                    <td className="p-3.5 font-bold text-bubblegum-deep whitespace-nowrap">
                      {s.scenario_id}
                    </td>
                    <td className="p-3.5 text-ink font-sans max-w-xs truncate" title={s.title}>
                      {s.title}
                    </td>
                    <td className="p-3.5 text-center">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          isPositive
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        }`}
                      >
                        {s.ground_truth_label}
                      </span>
                    </td>
                    <td className="p-3.5 text-right text-muted">
                      <span>{s.constant_0_65.probability.toFixed(2)}</span> /{" "}
                      <span className="text-ink font-semibold">{s.constant_0_65.brier.toFixed(4)}</span>
                    </td>
                    <td className="p-3.5 text-right text-muted">
                      <span>{s.base_rate.probability.toFixed(4)}</span> /{" "}
                      <span className="text-ink font-semibold">{s.base_rate.brier.toFixed(4)}</span>
                    </td>
                    <td className="p-3.5 text-right">
                      <span className="text-bubblegum-deep font-bold">{s.live_forecaster.probability.toFixed(2)}</span> /{" "}
                      <span className="text-emerald-700 font-bold">{s.live_forecaster.brier.toFixed(4)}</span>
                    </td>
                    <td className="p-3.5 text-center text-muted whitespace-nowrap">
                      <span>[{s.stability_check.runs.join(", ")}]</span>{" "}
                      <span className="text-emerald-700 font-bold">({s.stability_check.spread.toFixed(4)})</span>
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
