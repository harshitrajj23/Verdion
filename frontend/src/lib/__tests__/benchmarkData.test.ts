import { describe, it, expect } from "vitest";
import {
  validateBenchmarkData,
  computeDynamicallyComputedMeans,
} from "../benchmarkData";
import rawData from "@/data/results_train_live.json";

describe("Benchmark Data Loader and Validator", () => {
  it("successfully validates the live train benchmark JSON", () => {
    const result = validateBenchmarkData(rawData);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.metadata.eval_split).toBe("train");
      expect(result.data.metadata.scenario_count).toBe(14);
      expect(result.data.per_scenario.length).toBe(14);
    }
  });

  it("computes dynamic aggregate means matching expected Brier scores", () => {
    const result = validateBenchmarkData(rawData);
    expect(result.success).toBe(true);
    if (result.success) {
      const means = computeDynamicallyComputedMeans(result.data.per_scenario);
      expect(means.mean_constant).toBe(0.2511);
      expect(means.mean_base).toBe(0.2449);
      expect(means.mean_live).toBe(0.1611);
    }
  });

  it("rejects non-train evaluation split without fallbacks", () => {
    const invalid = {
      ...rawData,
      metadata: { ...rawData.metadata, eval_split: "test" },
    };
    const result = validateBenchmarkData(invalid);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toContain("Only 'train' split is supported");
    }
  });

  it("rejects payload missing required scenario metrics", () => {
    const invalid = {
      ...rawData,
      per_scenario: [
        {
          scenario_id: "scen_bad",
          title: "Bad scenario",
          ground_truth_label: 1,
          // missing constant_0_65, base_rate, live_forecaster
        },
      ],
    };
    const result = validateBenchmarkData(invalid);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toContain("is missing valid constant_0_65 metrics");
    }
  });

  it("rejects payload missing metadata section entirely", () => {
    const invalid = { per_scenario: rawData.per_scenario };
    const result = validateBenchmarkData(invalid);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toContain("Missing required 'metadata' section");
    }
  });
});
