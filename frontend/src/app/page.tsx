"use client";

import React from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import deployments from "@/lib/deployments.json";
import lifecycleSepolia from "@/lib/lifecycle_sepolia.json";
import resultsTrainLive from "@/data/results_train_live.json";
import {
  Briefcase,
  TrendingUp,
  Gift,
  Coins,
  ArrowRight,
  ExternalLink,
  Layers,
  FileCheck,
  CheckCircle2,
  Clock
} from "lucide-react";

export default function DashboardPage() {
  const { currentCase } = useStore();

  // 1. Prediction markets & settlement from lifecycle_sepolia.json
  const marketCount = lifecycleSepolia.marketId ? 1 : 0;
  const settledMarketCount = lifecycleSepolia.finalState?.marketStateName === "SETTLED" ? 1 : 0;
  // Brier computed from probBps 6500 (0.65) vs outcome true (1) = (0.65 - 1)^2 = 0.1225
  const prob = 6500 / 10000;
  const sepoliaBrier = Math.pow(prob - 1, 2).toFixed(4); // 0.1225

  // 2. Deployed contract count from deployments.json (5 contracts)
  const deployedContractCount = Object.keys(deployments.contracts).length; // 5

  // 3. Train benchmark mean Brier from results_train_live.json only (0.1611)
  const trainBenchmarkBrier = resultsTrainLive.aggregate_brier_scores.live_forecaster.toFixed(4); // 0.1611

  return (
    <div className="space-y-10 animate-fade-in-up">
      {/* ── Plain White Hero Section (Fraunces headline, 1 muted paragraph, 2 buttons) ── */}
      <section className="rounded-2xl bg-white p-8 sm:p-12 border border-hairline shadow-soft space-y-6">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold bg-bubblegum-soft text-bubblegum-deep border border-hairline">
            <span>Sepolia testnet, single-deployer demo</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-ink font-display leading-[1.12]">
            Evidence-Grounded Legal Risk Forecasting.
          </h1>

          <p className="text-base sm:text-lg text-muted font-normal leading-relaxed max-w-2xl font-sans">
            Autonomous multi-agent swarms, commit-reveal prediction markets, and verifiable cryptographic audit trails for European AI and data protection law.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link href="/markets" className="apple-btn-primary">
              <span>View Prediction Market</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/benchmark" className="apple-btn-secondary">
              <span>Inspect Benchmark Data</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Protocol Key Metrics Cards ── */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* Metric 1: Prediction Markets */}
        <div className="rounded-2xl bg-white p-6 border border-hairline shadow-soft space-y-2 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-muted">
              <span>Prediction Markets</span>
              <TrendingUp className="w-4 h-4 text-bubblegum" />
            </div>
            <div className="text-3xl font-semibold tracking-tight text-ink font-display">
              {marketCount} Market
            </div>
            <span className="inline-block text-[11px] font-semibold text-bubblegum-deep bg-bubblegum-soft px-2.5 py-0.5 rounded-full border border-hairline">
              {settledMarketCount} Settled, 0 Open
            </span>
          </div>
          <p className="text-[11px] font-mono text-muted pt-2 border-t border-hairline">
            Source: frontend/src/lib/lifecycle_sepolia.json
          </p>
        </div>

        {/* Metric 2: Sepolia Settlement Brier Score */}
        <div className="rounded-2xl bg-white p-6 border border-hairline shadow-soft space-y-2 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-muted">
              <span>Sepolia Market Brier Score</span>
              <Coins className="w-4 h-4 text-bubblegum" />
            </div>
            <div className="text-3xl font-semibold tracking-tight text-ink font-mono">
              {sepoliaBrier}
            </div>
            <span className="inline-block text-[11px] font-semibold text-bubblegum-deep bg-bubblegum-soft px-2.5 py-0.5 rounded-full border border-hairline">
              probBps 6500 vs outcome true
            </span>
          </div>
          <p className="text-[11px] font-mono text-muted pt-2 border-t border-hairline">
            Source: frontend/src/lib/lifecycle_sepolia.json
          </p>
        </div>

        {/* Metric 3: Deployed Contracts */}
        <div className="rounded-2xl bg-white p-6 border border-hairline shadow-soft space-y-2 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-muted">
              <span>Deployed Contracts</span>
              <Layers className="w-4 h-4 text-bubblegum" />
            </div>
            <div className="text-3xl font-semibold tracking-tight text-ink font-display">
              {deployedContractCount} Contracts
            </div>
            <span className="inline-block text-[11px] font-semibold text-bubblegum-deep bg-bubblegum-soft px-2.5 py-0.5 rounded-full border border-hairline">
              Sepolia Block {deployments.deployBlock}
            </span>
          </div>
          <p className="text-[11px] font-mono text-muted pt-2 border-t border-hairline">
            Source: frontend/src/lib/deployments.json
          </p>
        </div>

        {/* Metric 4: Train Benchmark Mean Brier */}
        <div className="rounded-2xl bg-white p-6 border border-hairline shadow-soft space-y-2 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-muted">
              <span>Train Benchmark Mean Brier</span>
              <FileCheck className="w-4 h-4 text-bubblegum" />
            </div>
            <div className="text-3xl font-semibold tracking-tight text-ink font-mono">
              {trainBenchmarkBrier}
            </div>
            <span className="inline-block text-[11px] font-semibold text-bubblegum-deep bg-bubblegum-soft px-2.5 py-0.5 rounded-full border border-hairline">
              14 scenarios, in-sample live_forecaster
            </span>
          </div>
          <p className="text-[11px] font-mono text-muted pt-2 border-t border-hairline">
            Source: results_train_live.json
          </p>
        </div>

        {/* Metric 5: Active Cases */}
        <div className="rounded-2xl bg-white p-6 border border-hairline shadow-soft space-y-2 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-muted">
              <span>Active Cases</span>
              <Briefcase className="w-4 h-4 text-bubblegum" />
            </div>
            <div className="text-2xl font-semibold tracking-tight text-ink font-display">
              None recorded
            </div>
            <span className="inline-block text-[11px] font-semibold text-muted bg-cloud px-2.5 py-0.5 rounded-full border border-hairline">
              No live case records
            </span>
          </div>
          <p className="text-[11px] font-mono text-muted pt-2 border-t border-hairline">
            Source: No live case source recorded
          </p>
        </div>

        {/* Metric 6: Evidence Bounties */}
        <div className="rounded-2xl bg-white p-6 border border-hairline shadow-soft space-y-2 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-muted">
              <span>Evidence Bounties</span>
              <Gift className="w-4 h-4 text-bubblegum" />
            </div>
            <div className="text-2xl font-semibold tracking-tight text-ink font-display">
              None recorded
            </div>
            <span className="inline-block text-[11px] font-semibold text-muted bg-cloud px-2.5 py-0.5 rounded-full border border-hairline">
              No live bounty records
            </span>
          </div>
          <p className="text-[11px] font-mono text-muted pt-2 border-t border-hairline">
            Source: No live bounty source recorded
          </p>
        </div>
      </section>

      {/* ── Sepolia Testnet Demo Spotlight ── */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* On-Chain Market Spotlight */}
        <div className="rounded-2xl bg-white p-6 sm:p-8 border border-hairline shadow-soft space-y-5">
          <div className="flex items-center justify-between border-b border-hairline pb-4">
            <div>
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                Sepolia Market
              </span>
              <h2 className="text-xl font-semibold text-ink mt-1.5 font-display tracking-tight">
                Settled Forecast Market
              </h2>
            </div>
            <span className="text-xs font-semibold text-bubblegum-deep bg-bubblegum-soft px-3 py-1 rounded-full border border-hairline">
              {lifecycleSepolia.finalState.marketStateName}
            </span>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted font-sans">
              Market ID & Target:
            </span>
            <div className="p-3.5 rounded-xl bg-cloud border border-hairline font-mono text-xs text-ink break-all">
              {lifecycleSepolia.marketId}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted font-medium">Evaluator Forecast Probability:</span>
              <span className="font-mono font-bold text-bubblegum-deep text-sm">65.0%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-bubblegum-soft overflow-hidden border border-hairline">
              <div className="h-full bg-bubblegum rounded-full" style={{ width: "65%" }} />
            </div>
            <div className="flex items-center justify-between text-[11px] text-muted">
              <span>Outcome: Confirmed (1)</span>
              <span>Brier: {sepoliaBrier}</span>
            </div>
          </div>

          <div className="pt-2">
            <Link href="/markets" className="apple-btn-secondary w-full justify-center text-xs py-2">
              <span>Inspect Market Lifecycle</span>
              <ArrowRight className="w-3.5 h-3.5 text-bubblegum-deep" />
            </Link>
          </div>
        </div>

        {/* On-Chain Deployed Smart Contracts */}
        <div className="rounded-2xl bg-white p-6 sm:p-8 border border-hairline shadow-soft space-y-5">
          <div className="flex items-center justify-between border-b border-hairline pb-4">
            <div>
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                EVM Core
              </span>
              <h2 className="text-xl font-semibold text-ink mt-1.5 font-display tracking-tight">
                Verified Deployed Contracts
              </h2>
            </div>
            <span className="text-xs font-semibold text-bubblegum-deep bg-bubblegum-soft px-3 py-1 rounded-full border border-hairline">
              Chain 11155111
            </span>
          </div>

          <div className="space-y-2.5 divide-y divide-hairline">
            {Object.entries(deployments.contracts).map(([name, info]) => (
              <div key={name} className="pt-2 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-ink">{name}</span>
                  <p className="font-mono text-[11px] text-muted">{info.address.slice(0, 10)}...{info.address.slice(-8)}</p>
                </div>
                <span className="text-[10px] font-mono text-bubblegum-deep bg-bubblegum-soft px-2 py-0.5 rounded-full border border-hairline">
                  Block {info.deployBlock}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <Link href="/audit" className="apple-btn-secondary w-full justify-center text-xs py-2">
              <span>View Full Audit Registry</span>
              <ArrowRight className="w-3.5 h-3.5 text-bubblegum-deep" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Sepolia Testnet Receipts Trail ── */}
      <section className="rounded-2xl bg-white p-6 sm:p-8 border border-hairline shadow-soft space-y-5">
        <div className="flex items-center justify-between border-b border-hairline pb-4">
          <div>
            <h2 className="text-xl font-semibold text-ink font-display tracking-tight">
              Sepolia Testnet Receipts Journal
            </h2>
            <p className="text-xs text-muted">
              Nine confirmed transactions executing the complete commit-reveal market lifecycle.
            </p>
          </div>
          <Link
            href="/audit"
            className="text-xs text-bubblegum-deep hover:underline flex items-center gap-1 font-semibold"
          >
            <span>Full Audit Explorer</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-hairline">
          {lifecycleSepolia.steps.map((step, idx) => (
            <div key={idx} className="py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                  {step.step}
                </span>
                <span className="font-mono text-ink text-[11px]">Block {step.blockNumber}</span>
              </div>
              <div className="flex items-center gap-4 text-muted">
                <a
                  href={`https://sepolia.etherscan.io/tx/${step.txHash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[11px] text-bubblegum-deep hover:underline flex items-center gap-1"
                >
                  <span>Tx: {step.txHash.slice(0, 10)}...{step.txHash.slice(-8)}</span>
                  <ExternalLink className="w-3 h-3 text-bubblegum" />
                </a>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Confirmed
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
