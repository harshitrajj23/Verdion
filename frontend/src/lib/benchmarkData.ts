export interface ScenarioResult {
  scenario_id: string;
  title: string;
  ground_truth_label: number;
  constant_0_65: {
    probability: number;
    brier: number;
  };
  base_rate: {
    probability: number;
    brier: number;
  };
  live_forecaster: {
    probability: number;
    brier: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    elapsed_ms?: number;
  };
  stability_check: {
    runs: number[];
    spread: number;
    is_stable: boolean;
  };
}

export interface BenchmarkMetadata {
  eval_split: string;
  scenario_count: number;
  utc_run_time: string;
  git_commit_hash: string;
  git_status_short?: string;
  prompt_sha256?: string;
  model_name: string;
  model_digest: string;
  quantization?: string;
  ollama_version: string;
  train_base_rate: number;
}

export interface StabilitySummary {
  total_scenarios: number;
  unstable_count: number;
  unstable_scenarios: string[];
  threshold: number;
  verdict: string;
}

export interface LiveBenchmarkData {
  metadata: BenchmarkMetadata;
  aggregate_brier_scores: {
    constant_0_65: number;
    base_rate: number;
    live_forecaster: number;
  };
  stability_summary: StabilitySummary;
  per_scenario: ScenarioResult[];
}

export type BenchmarkDataResult =
  | { success: true; data: LiveBenchmarkData }
  | { success: false; error: string };

/**
 * Validates the loaded JSON structure. Returns an explicit error object
 * if any required field is missing or invalid, avoiding silent fallbacks.
 */
export function validateBenchmarkData(raw: any): BenchmarkDataResult {
  if (!raw || typeof raw !== "object") {
    return { success: false, error: "Benchmark payload is empty or not a valid JSON object." };
  }

  const { metadata, per_scenario, aggregate_brier_scores, stability_summary } = raw;

  if (!metadata || typeof metadata !== "object") {
    return { success: false, error: "Missing required 'metadata' section." };
  }

  if (metadata.eval_split !== "train") {
    return {
      success: false,
      error: `Invalid evaluation split '${metadata.eval_split}'. Only 'train' split is supported.`,
    };
  }

  if (typeof metadata.scenario_count !== "number" || metadata.scenario_count <= 0) {
    return { success: false, error: "Invalid or missing 'metadata.scenario_count'." };
  }

  if (!metadata.git_commit_hash) {
    return { success: false, error: "Missing 'metadata.git_commit_hash'." };
  }

  if (!metadata.ollama_version) {
    return { success: false, error: "Missing 'metadata.ollama_version'." };
  }

  if (!Array.isArray(per_scenario) || per_scenario.length === 0) {
    return { success: false, error: "Missing or empty 'per_scenario' array." };
  }

  for (let i = 0; i < per_scenario.length; i++) {
    const s = per_scenario[i];
    if (!s.scenario_id) {
      return { success: false, error: `Scenario at index ${i} is missing 'scenario_id'.` };
    }
    if (s.ground_truth_label !== 0 && s.ground_truth_label !== 1) {
      return {
        success: false,
        error: `Scenario ${s.scenario_id} has invalid ground_truth_label: ${s.ground_truth_label}.`,
      };
    }
    if (!s.constant_0_65 || typeof s.constant_0_65.probability !== "number" || typeof s.constant_0_65.brier !== "number") {
      return { success: false, error: `Scenario ${s.scenario_id} is missing valid constant_0_65 metrics.` };
    }
    if (!s.base_rate || typeof s.base_rate.probability !== "number" || typeof s.base_rate.brier !== "number") {
      return { success: false, error: `Scenario ${s.scenario_id} is missing valid base_rate metrics.` };
    }
    if (!s.live_forecaster || typeof s.live_forecaster.probability !== "number" || typeof s.live_forecaster.brier !== "number") {
      return { success: false, error: `Scenario ${s.scenario_id} is missing valid live_forecaster metrics.` };
    }
    if (!s.stability_check || !Array.isArray(s.stability_check.runs) || typeof s.stability_check.spread !== "number") {
      return { success: false, error: `Scenario ${s.scenario_id} is missing valid stability_check.` };
    }
  }

  return { success: true, data: raw as LiveBenchmarkData };
}

/**
 * Computes mean Brier scores directly from scenario items.
 */
export function computeDynamicallyComputedMeans(scenarios: ScenarioResult[]) {
  if (scenarios.length === 0) {
    return { mean_constant: 0, mean_base: 0, mean_live: 0 };
  }
  const sum_const = scenarios.reduce((acc, s) => acc + s.constant_0_65.brier, 0);
  const sum_base = scenarios.reduce((acc, s) => acc + s.base_rate.brier, 0);
  const sum_live = scenarios.reduce((acc, s) => acc + s.live_forecaster.brier, 0);
  const n = scenarios.length;

  return {
    mean_constant: Number((sum_const / n).toFixed(4)),
    mean_base: Number((sum_base / n).toFixed(4)),
    mean_live: Number((sum_live / n).toFixed(4)),
  };
}

export interface DiscriminationAnalysis {
  mean_p_pos: number;
  mean_p_neg: number;
  separation: number;
  ci_lower: number;
  ci_upper: number;
  includes_zero: boolean;
}

/**
 * Computes class separation [mean_p(1) - mean_p(0)] and a 95% bootstrap confidence interval
 * for (forecaster mean Brier - base-rate mean Brier) over scenarios, labeled in-sample, train only.
 */
export function computeDiscriminationAndBootstrap(
  scenarios: ScenarioResult[],
  nResamples: number = 10000,
  seed: number = 20261019
): DiscriminationAnalysis {
  const pos = scenarios.filter((s) => s.ground_truth_label === 1);
  const neg = scenarios.filter((s) => s.ground_truth_label === 0);

  const mean_p_pos = pos.length > 0 ? pos.reduce((acc, s) => acc + s.live_forecaster.probability, 0) / pos.length : 0;
  const mean_p_neg = neg.length > 0 ? neg.reduce((acc, s) => acc + s.live_forecaster.probability, 0) / neg.length : 0;
  const separation = Number((mean_p_pos - mean_p_neg).toFixed(4));

  let a = seed;
  const rand = () => {
    let t = (a += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };

  const n = scenarios.length;
  const deltas: number[] = [];

  for (let b = 0; b < nResamples; b++) {
    let b_fc = 0;
    let b_base = 0;
    for (let i = 0; i < n; i++) {
      const idx = Math.floor(rand() * n);
      b_fc += scenarios[idx].live_forecaster.brier;
      b_base += scenarios[idx].base_rate.brier;
    }
    deltas.push((b_fc - b_base) / n);
  }

  deltas.sort((x, y) => x - y);
  const ci_lower = Number(deltas[Math.floor(0.025 * nResamples)].toFixed(4));
  const ci_upper = Number(deltas[Math.floor(0.975 * nResamples)].toFixed(4));
  const includes_zero = ci_lower <= 0 && ci_upper >= 0;

  return {
    mean_p_pos: Number(mean_p_pos.toFixed(4)),
    mean_p_neg: Number(mean_p_neg.toFixed(4)),
    separation,
    ci_lower,
    ci_upper,
    includes_zero,
  };
}
