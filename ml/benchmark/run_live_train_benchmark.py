from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
import urllib.request

from ml.agents.agent_swarm import VerdionAgentSwarm
from ml.aggregation.scoring import brier


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"


def get_git_status_short() -> str:
    try:
        res = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"


def get_ollama_version() -> str:
    try:
        req = urllib.request.Request("http://localhost:11434/api/version")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("version", "unknown")
    except Exception:
        return "unknown"


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(base_dir))
    scenarios_path = os.path.join(base_dir, "scenarios.json")
    out_file = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(base_dir, "results_train_live.json")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        all_scenarios = json.load(f)

    # Filter train split only (14 scenarios) - NEVER run held_out
    train_scenarios = [s for s in all_scenarios if s.get("split") == "train"]
    train_scenarios = sorted(train_scenarios, key=lambda s: s.get("scenario_id") or s.get("id"))

    labels = [s["ground_truth_label"] for s in train_scenarios]
    train_base_rate = round(sum(labels) / len(labels), 4)

    git_commit = get_git_commit()
    git_status = get_git_status_short()
    ollama_ver = get_ollama_version()
    model_name = "qwen2.5:7b-instruct"
    model_digest = "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"
    quantization = "Q4_K_M"

    # Compute prompt SHA-256
    prompts_text = (
        "Researcher: Retrieve and organize relevant authority into verifiable factual propositions. "
        "Interpreter: Maps facts to statutory requirements and identifies gaps. "
        "Adversarial: Generates legally plausible counterarguments. "
        "Forecaster: Forecasts probability of adverse compliance finding."
    )
    prompt_sha256 = hashlib.sha256(prompts_text.encode("utf-8")).hexdigest()
    utc_start_time = datetime.now(timezone.utc).isoformat()

    swarm = VerdionAgentSwarm()

    print(f"Starting Live Train Pipeline Benchmark on {len(train_scenarios)} train scenarios...")
    print(f"Git commit: {git_commit}")
    print(f"Ollama model: {model_name} ({quantization}) on Ollama v{ollama_ver}")
    print(f"Train base rate: {train_base_rate} (8/14)")
    print("=" * 100)
    sys.stdout.flush()

    per_scenario_results = []
    brier_const_list = []
    brier_base_list = []
    brier_live_list = []

    for idx, s in enumerate(train_scenarios, 1):
        sid = s.get("scenario_id") or s.get("id")
        title = s.get("title", "")
        y = s["ground_truth_label"]
        print(f"\n[{idx}/14] Processing {sid}: '{title}' (Label = {y})")
        sys.stdout.flush()

        # Step A: Run live upstream roles
        t0 = time.perf_counter()
        res = swarm.run_legal_researcher(s)
        t_res = time.perf_counter() - t0

        t0 = time.perf_counter()
        interp = swarm.run_legal_interpreter(s, res)
        t_int = time.perf_counter() - t0

        t0 = time.perf_counter()
        adv = swarm.run_adversarial_researcher(s, interp)
        t_adv = time.perf_counter() - t0

        upstream = [res, interp, adv]

        # Step B: Run Forecaster 3 times for stability analysis
        print(f"  Upstream finished (Res: {t_res:.1f}s, Int: {t_int:.1f}s, Adv: {t_adv:.1f}s). Running Forecaster (3 runs)...")
        sys.stdout.flush()

        fc_runs = []
        for r_num in (1, 2, 3):
            t0 = time.perf_counter()
            fc = swarm.run_quantitative_forecaster(s, upstream_outputs=upstream)
            elapsed = time.perf_counter() - t0
            p = float(fc.get("forecast", {}).get("probability", 0.5))
            m = fc.get("execution_metrics", {})
            fc_runs.append({
                "run": r_num,
                "probability": round(p, 4),
                "event_definition": fc.get("forecast", {}).get("event_definition", ""),
                "prompt_tokens": m.get("prompt_tokens", 0),
                "completion_tokens": m.get("completion_tokens", 0),
                "elapsed_ms": m.get("elapsed_ms", round(elapsed * 1000, 2)),
            })
            print(f"    Forecaster run {r_num}: p = {p:.4f} ({elapsed:.1f}s)")
            sys.stdout.flush()

        probs = [r["probability"] for r in fc_runs]
        spread = round(max(probs) - min(probs), 4)
        is_stable = spread <= 0.05

        # Main live pipeline probability is Run 1
        p_live = probs[0]
        bs_live = brier(p_live, y)
        brier_live_list.append(bs_live)

        # Baseline 1: Constant 0.65
        p_const = 0.65
        bs_const = brier(p_const, y)
        brier_const_list.append(bs_const)

        # Baseline 2: Base Rate
        p_base = train_base_rate
        bs_base = brier(p_base, y)
        brier_base_list.append(bs_base)

        record = {
            "scenario_id": sid,
            "title": title,
            "ground_truth_label": y,
            "constant_0_65": {"probability": p_const, "brier": bs_const},
            "base_rate": {"probability": p_base, "brier": bs_base},
            "live_forecaster": {
                "probability": p_live,
                "brier": bs_live,
                "prompt_tokens": fc_runs[0]["prompt_tokens"],
                "completion_tokens": fc_runs[0]["completion_tokens"],
                "elapsed_ms": fc_runs[0]["elapsed_ms"],
            },
            "stability_check": {
                "runs": probs,
                "spread": spread,
                "is_stable": is_stable,
            },
        }
        per_scenario_results.append(record)

    mean_brier_const = round(sum(brier_const_list) / len(brier_const_list), 4)
    mean_brier_base = round(sum(brier_base_list) / len(brier_base_list), 4)
    mean_brier_live = round(sum(brier_live_list) / len(brier_live_list), 4)

    unstable_scenarios = [r["scenario_id"] for r in per_scenario_results if not r["stability_check"]["is_stable"]]

    final_payload = {
        "metadata": {
            "eval_split": "train",
            "scenario_count": len(train_scenarios),
            "utc_run_time": utc_start_time,
            "git_commit_hash": git_commit,
            "git_status_short": git_status,
            "prompt_sha256": prompt_sha256,
            "model_name": model_name,
            "model_digest": model_digest,
            "quantization": quantization,
            "ollama_version": ollama_ver,
            "train_base_rate": train_base_rate,
        },
        "aggregate_brier_scores": {
            "constant_0_65": mean_brier_const,
            "base_rate": mean_brier_base,
            "live_forecaster": mean_brier_live,
        },
        "stability_summary": {
            "total_scenarios": len(train_scenarios),
            "unstable_count": len(unstable_scenarios),
            "unstable_scenarios": unstable_scenarios,
            "threshold": 0.05,
            "verdict": "UNSTABLE" if unstable_scenarios else "STABLE",
        },
        "per_scenario": per_scenario_results,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    print("\n" + "=" * 115)
    print("STAGE 2: LIVE PIPELINE ON TRAIN SPLIT RESULTS")
    print("=" * 115)
    print(f"{'Scenario ID':<12} | {'Label':<5} | {'Constant 0.65':<16} | {'Base Rate (8/14)':<18} | {'Live Forecaster':<18} | {'Forecaster Brier'}")
    print("-" * 115)
    for r in per_scenario_results:
        sid = r["scenario_id"]
        y = r["ground_truth_label"]
        c_p = f"{r['constant_0_65']['probability']:.2f} (BS:{r['constant_0_65']['brier']:.4f})"
        b_p = f"{r['base_rate']['probability']:.4f} (BS:{r['base_rate']['brier']:.4f})"
        l_p = f"{r['live_forecaster']['probability']:.4f}"
        bs_l = f"{r['live_forecaster']['brier']:.4f}"
        print(f"{sid:<12} | {y:<5} | {c_p:<16} | {b_p:<18} | {l_p:<18} | {bs_l}")
    print("-" * 115)
    print(f"{'AGGREGATE':<12} | {'-':<5} | Mean BS: {mean_brier_const:<7} | Mean BS: {mean_brier_base:<9} | Mean BS: {mean_brier_live:<9} | -")
    print("=" * 115)

    print("\n" + "=" * 115)
    print("STAGE 3: FORECASTER STABILITY AUDIT (3 Identical Runs per Scenario)")
    print("=" * 115)
    print(f"{'Scenario ID':<12} | {'Run 1':<8} | {'Run 2':<8} | {'Run 3':<8} | {'Spread (Max-Min)':<18} | {'Stable (Spread <= 0.05)?'}")
    print("-" * 115)
    for r in per_scenario_results:
        sid = r["scenario_id"]
        runs = r["stability_check"]["runs"]
        spread = r["stability_check"]["spread"]
        st = "YES" if r["stability_check"]["is_stable"] else "NO (UNSTABLE)"
        print(f"{sid:<12} | {runs[0]:<8.4f} | {runs[1]:<8.4f} | {runs[2]:<8.4f} | {spread:<18.4f} | {st}")
    print("-" * 115)
    print(f"Total Unstable Scenarios (Spread > 0.05): {len(unstable_scenarios)} of 14")
    if unstable_scenarios:
        print("VERDICT: Forecaster is UNSTABLE across identical inputs. Single-run values cannot be relied upon for Brier comparison.")
    else:
        print("VERDICT: Forecaster is STABLE across identical inputs.")
    print("=" * 115)
    print(f"\nResults successfully written to: {out_file}")


if __name__ == "__main__":
    main()
