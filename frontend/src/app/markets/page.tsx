"use client";

import React, { useState } from "react";
import { useStore } from "@/lib/store";
import { TransactionStatus } from "@/components/TransactionStatus";
import { DeadlineCountdown } from "@/components/DeadlineCountdown";
import { EmptyState } from "@/components/EmptyState";
import {
  TrendingUp,
  ShieldCheck,
  Clock,
  Coins,
  AlertTriangle,
  Lock,
  Unlock,
  KeyRound,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Users
} from "lucide-react";

import { api } from "@/lib/api";
import deployments from "@/lib/deployments.json";
import lifecycleSepolia from "@/lib/lifecycle_sepolia.json";

export default function PredictionMarketsPage() {
  const {
    markets,
    commitForecast,
    revealForecast,
    challengeResolution,
    settleMarket,
    walletAddress,
    pendingTxs,
    isLiveChain
  } = useStore();

  const [selectedMarketId, setSelectedMarketId] = useState<string>("");
  const [probInput, setProbInput] = useState<number>(70);
  const [nonceInput, setNonceInput] = useState<string>(
    "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [challengeReason, setChallengeReason] = useState("");
  const [evalMetrics, setEvalMetrics] = useState<any | null>(null);

  React.useEffect(() => {
    api.getForecastingEvaluation().then((res) => {
      setEvalMetrics(res);
    }).catch(() => {});
  }, []);

  const activeMarketId = selectedMarketId && markets.some((m) => m.market_id === selectedMarketId)
    ? selectedMarketId
    : (markets[0]?.market_id || "");
  const market = markets.find((m) => m.market_id === activeMarketId) || markets[0];
  const relevantTxs = pendingTxs.filter(
    (tx) => tx.action.includes("Forecast") || tx.action.includes("Market") || tx.action.includes("Challenge")
  );

  if (!market) {
    return (
      <EmptyState
        icon={<TrendingUp className="w-7 h-7 text-lavender-600" />}
        title="No Prediction Markets Available"
        description="No markets have been created for this case yet. Markets are generated when agents commit probability forecasts."
      />
    );
  }

  const handleCommit = async () => {
    setIsSubmitting(true);
    try {
      await commitForecast(market.market_id, probInput / 100, nonceInput);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReveal = async () => {
    setIsSubmitting(true);
    try {
      await revealForecast(market.market_id, probInput / 100, nonceInput);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChallenge = async () => {
    if (!challengeReason) return;
    setIsSubmitting(true);
    try {
      await challengeResolution(market.market_id, challengeReason);
      setChallengeReason("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSettle = async () => {
    setIsSubmitting(true);
    try {
      await settleMarket(market.market_id);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeDeadline =
    market.state === "PUBLISHED" || market.state === "DRAFT"
      ? { deadline: market.commit_deadline, label: "Commit Deadline", accent: "cyan" as const }
      : market.state === "REVEAL"
      ? { deadline: market.reveal_deadline, label: "Reveal Deadline", accent: "amber" as const }
      : market.state === "RESOLUTION_PROPOSED" || market.state === "CHALLENGE"
      ? { deadline: market.challenge_deadline, label: "Challenge Deadline", accent: "rose" as const }
      : null;

  const stateColor =
    market.state === "SETTLED"
      ? "bg-bubblegum-soft text-bubblegum-deep border-hairline font-semibold"
      : market.state === "VOID"
      ? "bg-cloud text-muted border-hairline"
      : market.state === "CHALLENGE"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : "bg-bubblegum-soft/60 text-bubblegum-deep border-hairline font-semibold";

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* ── Header Card ── */}
      <div className="apple-card space-y-5 border border-hairline shadow-soft bg-white">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                §16.5
              </span>
              <h1 className="text-2xl sm:text-3xl font-semibold text-ink tracking-tight font-display">
                Prediction Market Protocol
              </h1>
            </div>
            <p className="text-xs text-muted mt-1">
              Commit-reveal probabilistic forecast aggregation over objectively resolvable evaluation outcomes.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-medium text-bubblegum-deep bg-bubblegum-soft/60 border border-hairline px-3.5 py-1.5 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 text-bubblegum shrink-0" />
            <span>Empirical event forecasts, not final legal determinations</span>
          </div>
        </div>

        {/* REQUIRED CAVEAT CARD: Visible, Not Collapsed */}
        <div className="p-4 rounded-[16px] bg-bubblegum-soft/30 border border-hairline shadow-soft space-y-1.5">
          <div className="flex items-center gap-2 font-semibold text-bubblegum-deep text-xs font-display">
            <AlertTriangle className="w-4 h-4 text-bubblegum shrink-0" />
            <span>Protocol Disclosure & Settlement Caveat</span>
          </div>
          <p className="text-xs text-ink leading-relaxed font-sans">
            Event definition: forecaster estimates the probability of an evaluator-proposed compliance gap. Settlement in this demo was performed by a single deployer acting as agent and evaluator.
          </p>
        </div>

        {/* Market Selector Tabs */}
        <div className="inline-flex p-1 rounded-full bg-cloud border border-hairline max-w-full overflow-x-auto scrollbar-none">
          {markets.map((m) => (
            <button
              key={m.market_id}
              onClick={() => setSelectedMarketId(m.market_id)}
              className={`px-4 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 transition-all duration-150 active:scale-[0.97] ${
                selectedMarketId === m.market_id
                  ? "bg-white text-ink shadow-soft border border-hairline font-semibold"
                  : "text-muted hover:text-ink hover:bg-white/60"
              }`}
            >
              <span>{m.market_id}</span>
              {m.is_recorded_sepolia ? (
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep font-semibold border border-hairline">
                  Sepolia testnet, single-deployer demo
                </span>
              ) : (
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-cloud text-muted font-bold border border-hairline uppercase tracking-wider">
                  No live data
                </span>
              )}
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cloud text-muted font-mono">
                {m.state}
              </span>
            </button>
          ))}
        </div>

        {/* Protocol Disclosures & Architecture Transparency */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-hairline">
          <div className="p-3.5 rounded-[14px] bg-cloud border border-hairline space-y-1 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-bubblegum-deep font-display">
              <Users className="w-3.5 h-3.5" />
              <span>Demonstration Architecture Disclosure</span>
            </div>
            <p className="text-muted leading-relaxed text-[11px]">
              The recorded Sepolia on-chain lifecycle (<span className="font-mono text-ink">{lifecycleSepolia.marketId.slice(0, 8)}...{lifecycleSepolia.marketId.slice(-6)}</span>) was executed with deployer account (<span className="font-mono text-ink">{lifecycleSepolia.deployer.slice(0, 8)}...{lifecycleSepolia.deployer.slice(-4)}</span>) on contract <span className="font-mono text-ink">{deployments.contracts.PredictionMarket.address.slice(0, 8)}...</span> acting as both agent and evaluator. Multi-agent panels (<span className="font-semibold text-ink">N = 3</span>) represent simulated benchmark scenarios to demonstrate protocol aggregation.
            </p>
          </div>

          <div className="p-3.5 rounded-[14px] bg-cloud border border-hairline space-y-1 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-bubblegum-deep font-display">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Limitation 3: Event-Definition Mismatch</span>
            </div>
            <p className="text-muted leading-relaxed text-[11px]">
              Upstream ML forecasters predict general GDPR/EU AI Act liability outcomes, whereas <span className="font-mono text-ink">PredictionMarket</span> resolves on specific evaluator rubric gap findings. Operational deployment requires alignment between question syntax and on-chain rubric criteria.
            </p>
          </div>
        </div>

        {/* Option C Empirical Forecasting Calibration & Proper Scoring Card */}
        {evalMetrics && (
          <div className="pt-4 border-t border-hairline space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                  Option C Benchmark
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cloud text-muted border border-hairline uppercase tracking-wider">
                  No live data
                </span>
                <h3 className="text-sm font-bold text-ink font-display">Empirical Forecasting Evaluation & Calibration</h3>
              </div>
              <span className="text-[11px] text-muted font-mono">
                {evalMetrics.total_resolved_forecasts} Resolved Forecasts Across {evalMetrics.resolved_markets_count} Markets
              </span>
            </div>

            {/* Score Metrics */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-[12px] bg-cloud border border-hairline space-y-0.5">
                <span className="text-[10px] text-muted">Brier Score:</span>
                <div className="font-mono font-bold text-base text-bubblegum-deep">
                  {evalMetrics.protocol_metrics?.brier_score ?? 0.25}
                </div>
                <span className="text-[9px] text-muted">vs 0.25 (Uniform Baseline)</span>
              </div>
              <div className="p-3 rounded-[12px] bg-cloud border border-hairline space-y-0.5">
                <span className="text-[10px] text-muted">Binary Log Loss:</span>
                <div className="font-mono font-bold text-base text-ink">
                  {evalMetrics.protocol_metrics?.log_loss ?? 0.6931}
                </div>
                <span className="text-[9px] text-muted">Cross-entropy clipping</span>
              </div>
              <div className="p-3 rounded-[12px] bg-cloud border border-hairline space-y-0.5">
                <span className="text-[10px] text-muted">Calibration Error (ECE):</span>
                <div className="font-mono font-bold text-base text-emerald-700">
                  {evalMetrics.protocol_metrics?.expected_calibration_error ?? 0.0}
                </div>
                <span className="text-[9px] text-muted">Across 5 probability bins</span>
              </div>
              <div className="p-3 rounded-[12px] bg-cloud border border-hairline space-y-0.5">
                <span className="text-[10px] text-muted">Historical Base Rate:</span>
                <div className="font-mono font-bold text-base text-ink">
                  {((evalMetrics.historical_base_rate ?? 0.5) * 100).toFixed(1)}%
                </div>
                <span className="text-[9px] text-muted">Observed positive frequency</span>
              </div>
            </div>

            {/* Calibration Bins Breakdown */}
            {evalMetrics.calibration_curve && evalMetrics.calibration_curve.length > 0 && (
              <div className="p-3 rounded-[12px] bg-cloud border border-hairline space-y-2">
                <span className="text-[11px] font-semibold text-ink block font-display">Reliability Diagram (Calibration by Bin):</span>
                <div className="grid grid-cols-5 gap-2 text-center text-[10px]">
                  {evalMetrics.calibration_curve.map((bin: any, idx: number) => (
                    <div key={idx} className="p-2 rounded-lg bg-white border border-hairline space-y-1">
                      <span className="font-mono font-semibold text-bubblegum-deep block">{bin.bin_range}</span>
                      <div className="text-muted">Count: <strong>{bin.count}</strong></div>
                      <div className="text-[9px] text-ink-secondary">
                        Obs: {(bin.observed_frequency * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Statistical Warning */}
            <p className="text-[10px] text-muted leading-relaxed italic">
              {evalMetrics.statistical_disclosure}
            </p>
          </div>
        )}
      </div>

      {/* Pending Transactions Feed */}
      {relevantTxs.length > 0 && (
        <div className="space-y-2">
          {relevantTxs.slice(0, 3).map((tx) => (
            <TransactionStatus
              key={tx.id}
              txHash={tx.txHash}
              state={tx.state}
              action={tx.action}
            />
          ))}
        </div>
      )}

      {/* Main Market View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2 cols): Event Definition & Revealed Forecasts */}
        <div className="lg:col-span-2 space-y-6">
          <div className="apple-card space-y-5 border border-hairline shadow-soft bg-white">
            <div className="flex items-start justify-between gap-3 border-b border-hairline pb-4">
              <div>
                <span className="text-[11px] font-mono text-bubblegum-deep uppercase font-semibold">
                  {market.market_id} • Case {market.case_id}
                </span>
                <h2 className="text-xl font-semibold text-ink mt-1 font-display tracking-tight">{market.question}</h2>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border shrink-0 ${stateColor}`}>
                {market.state}
              </span>
            </div>

            {/* Outcome Definition & Resolution Rules (§10.2) */}
            <div className="space-y-3 text-xs">
              <div className="p-4 rounded-[14px] bg-cloud border border-hairline space-y-1">
                <span className="text-muted font-semibold block uppercase tracking-wider text-[10px] font-display">
                  Precise Outcome Definition:
                </span>
                <p className="text-ink leading-relaxed">{market.outcome_definition}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-[12px] bg-cloud border border-hairline space-y-0.5">
                  <span className="text-[10px] text-muted font-medium">Resolution Source:</span>
                  <p className="font-semibold text-ink">{market.resolution_source}</p>
                </div>
                <div className="p-3.5 rounded-[12px] bg-cloud border border-hairline space-y-0.5">
                  <span className="text-[10px] text-muted font-medium">Authorized Evaluator:</span>
                  <p className="font-mono text-bubblegum-deep truncate">{market.evaluator_address}</p>
                </div>
              </div>
            </div>

            {/* Active Deadline Countdown */}
            {activeDeadline && (
              <DeadlineCountdown
                deadline={activeDeadline.deadline}
                label={activeDeadline.label}
                accent={activeDeadline.accent}
              />
            )}

            {/* Aggregate Statistics */}
            <div className="p-5 rounded-[16px] bg-cloud border border-hairline space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-secondary">Aggregated Belief Probability:</span>
                <span className="text-3xl font-bold font-mono text-bubblegum-deep">
                  {(market.aggregate_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-bubblegum-soft overflow-hidden border border-hairline">
                <div
                  className="h-full bg-bubblegum rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${market.aggregate_probability * 100}%` }}
                />
              </div>
              <div className="flex flex-wrap items-center justify-between text-xs text-muted pt-1">
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-bubblegum-deep" />
                  Sample Size: <strong className="text-ink font-medium">N = {market.sample_size} {market.is_recorded_sepolia ? "Agent (Single Deployer Demo)" : "Agents (Simulated)"}</strong>
                </span>
                <span>Disagreement Variance: <strong className="font-mono text-ink font-medium">{market.disagreement_variance}</strong></span>
                <span>Rule: <strong className="text-ink font-medium">Brier Proper Scoring</strong></span>
              </div>
            </div>

            {/* Revealed Forecasts Table */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold text-muted uppercase tracking-wider font-display">
                Revealed Forecast Register ({market.revealed_forecasts.length})
              </h3>
              {market.revealed_forecasts.length === 0 ? (
                <EmptyState
                  icon={<Lock className="w-6 h-6 text-bubblegum" />}
                  title="No Forecasts Revealed Yet"
                  description="Forecasts will appear here once the reveal deadline is reached and agents disclose their committed probabilities."
                />
              ) : (
                <div className="overflow-x-auto rounded-[14px] border border-hairline">
                  <table className="w-full text-left text-xs border-collapse bg-white">
                    <thead>
                      <tr className="border-b border-hairline bg-cloud text-muted font-semibold text-[10px] uppercase">
                        <th className="py-3 px-3.5">Agent</th>
                        <th className="py-3 px-3.5">Address</th>
                        <th className="py-3 px-3.5">Probability</th>
                        <th className="py-3 px-3.5">Evidence Digest</th>
                        <th className="py-3 px-3.5">Revealed Time</th>
                        <th className="py-3 px-3.5">Brier Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-hairline">
                      {market.revealed_forecasts.map((f, i) => (
                        <tr key={i} className="hover:bg-cloud/60 transition-colors">
                          <td className="py-3 px-3.5 font-semibold text-ink">{f.agent_id}</td>
                          <td className="py-3 px-3.5 font-mono text-[10px] text-bubblegum-deep">
                            {f.agent_address.slice(0, 8)}...{f.agent_address.slice(-4)}
                          </td>
                          <td className="py-3 px-3.5 font-mono font-bold text-bubblegum-deep text-sm">
                            {(f.probability * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-3.5 font-mono text-[10px] text-muted">
                            {f.evidence_digest.slice(0, 10)}...{f.evidence_digest.slice(-6)}
                          </td>
                          <td className="py-3 px-3.5 text-[11px] text-ink-secondary">
                            {new Date(f.revealed_at).toLocaleTimeString()}
                          </td>
                          <td className="py-3 px-3.5 font-mono text-[11px]">
                            {f.brier_score !== undefined ? (
                              <span className="text-bubblegum-deep font-semibold">{f.brier_score.toFixed(4)}</span>
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Settlement Tx (if settled) */}
            {market.settlement_tx && (
              <div className="p-3.5 rounded-[12px] bg-bubblegum-soft/30 border border-hairline flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-bubblegum" />
                  <span className="font-semibold text-bubblegum-deep">
                    {market.is_recorded_sepolia ? "Market Settled On-Chain (Sepolia)" : "Market Settled (Simulated Benchmark)"}
                  </span>
                </div>
                {market.is_recorded_sepolia ? (
                  <a
                    href={`https://sepolia.etherscan.io/tx/${market.settlement_tx}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-[11px] text-bubblegum-deep hover:underline flex items-center gap-1 font-medium"
                  >
                    <span>{market.settlement_tx.slice(0, 14)}...{market.settlement_tx.slice(-8)}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="font-mono text-[11px] text-muted">
                    {market.settlement_tx.slice(0, 14)}... (Simulated)
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right (1 col): Interactive Commit & Reveal Form (§10.4) */}
        <div className="space-y-6">
          {/* Commit / Reveal Terminal Card */}
          <div className="apple-card space-y-4 border border-hairline shadow-soft bg-white">
            <h3 className="text-base font-semibold text-ink flex items-center gap-2 font-display">
              <Lock className="w-4 h-4 text-bubblegum" />
              <span>Commit-Reveal Terminal (§10.4)</span>
            </h3>

            {!isLiveChain && (
              <div className="p-2.5 rounded-[10px] bg-bubblegum-soft/30 border border-hairline text-[11px] text-ink-secondary flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-bubblegum shrink-0" />
                <span>Sample mode — actions update local store only.</span>
              </div>
            )}

            <div className="space-y-3.5 text-xs">
              <div>
                <label className="text-ink-secondary font-medium block mb-1">
                  Forecast Probability: <span className="text-bubblegum-deep font-mono font-bold text-sm">{probInput}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={probInput}
                  onChange={(e) => setProbInput(Number(e.target.value))}
                  className="w-full accent-bubblegum cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-muted mt-0.5">
                  <span>0% (NO)</span>
                  <span>100% (YES)</span>
                </div>
              </div>

              <div>
                <label className="text-ink-secondary font-medium block mb-1 flex items-center justify-between">
                  <span>Secret Nonce (Entropy Salt):</span>
                  <button
                    onClick={() =>
                      setNonceInput(
                        "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")
                      )
                    }
                    className="text-[11px] text-bubblegum-deep hover:underline font-medium"
                  >
                    Generate New
                  </button>
                </label>
                <input
                  type="text"
                  value={nonceInput}
                  onChange={(e) => setNonceInput(e.target.value)}
                  className="w-full p-2.5 rounded-[10px] bg-cloud border border-hairline font-mono text-[10px] text-ink focus:outline-none focus:border-bubblegum transition-colors"
                />
              </div>

              <div className="p-3 rounded-[10px] bg-bubblegum-soft/30 border border-hairline space-y-1">
                <span className="text-[10px] font-mono text-muted block font-semibold">Commitment Formula:</span>
                <p className="font-mono text-[9px] text-ink-secondary leading-tight break-all">
                  keccak256(chainId, marketId, agent, prob, digest, nonce)
                </p>
              </div>

              {/* Action Buttons: Apple Pills */}
              <div className="pt-2 space-y-2">
                <button
                  onClick={handleCommit}
                  disabled={isSubmitting || market.state === "SETTLED" || market.state === "VOID"}
                  className="apple-btn-primary w-full py-2.5 justify-center disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner w-3.5 h-3.5 text-white" />
                      Broadcasting...
                    </>
                  ) : (
                    "1. Commit Forecast Hash"
                  )}
                </button>

                <button
                  onClick={handleReveal}
                  disabled={isSubmitting || market.state === "SETTLED" || market.state === "VOID"}
                  className="apple-btn-secondary w-full py-2.5 justify-center disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner w-3.5 h-3.5 text-bubblegum" />
                      Verifying...
                    </>
                  ) : (
                    "2. Reveal Forecast Secret"
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Evaluator & Settlement Console */}
          <div className="apple-card space-y-4 border border-hairline shadow-soft bg-white">
            <h3 className="text-base font-semibold text-ink flex items-center gap-2 font-display">
              <ShieldCheck className="w-4 h-4 text-bubblegum" />
              <span>Resolution & Settlement Console</span>
            </h3>

            {market.challenge_status.is_challenged && (
              <div className="p-3 rounded-[10px] bg-rose-50 border border-rose-200 text-xs space-y-1">
                <div className="flex items-center gap-1.5 text-rose-800 font-semibold">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>Resolution Challenged</span>
                </div>
                {market.challenge_status.challenger && (
                  <div className="font-mono text-[10px] text-muted">
                    By: {market.challenge_status.challenger.slice(0, 10)}...
                  </div>
                )}
                {market.challenge_status.reason && (
                  <p className="text-[11px] text-rose-900">{market.challenge_status.reason}</p>
                )}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-ink-secondary font-medium block">Dispute / Challenge Reason:</label>
                <input
                  type="text"
                  placeholder="e.g. Incompatible EDPB interpretation"
                  value={challengeReason}
                  onChange={(e) => setChallengeReason(e.target.value)}
                  className="w-full p-2.5 rounded-[10px] bg-cloud border border-hairline text-xs text-ink focus:outline-none focus:border-rose-400 transition-colors"
                />
              </div>

              <p className="text-[11px] text-amber-900 bg-amber-50 p-2.5 rounded-[10px] border border-amber-200">
                Note: In this MVP, challenges are resolved by the protocol admin evaluator.
              </p>

              <button
                onClick={handleChallenge}
                disabled={!challengeReason || isSubmitting || market.state === "SETTLED"}
                className="apple-btn-ghost w-full py-2 justify-center border-rose-300 text-rose-700 hover:bg-rose-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Submit Resolution Challenge (FR-046)
              </button>

              <button
                onClick={handleSettle}
                disabled={isSubmitting || market.state === "SETTLED"}
                className="apple-btn-secondary w-full py-2 justify-center disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Execute Proper Scoring Settlement (FR-048)
              </button>
            </div>
          </div>

          {/* Deadline Info Panel */}
          <div className="apple-card space-y-3 border border-hairline shadow-soft bg-white">
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wider flex items-center gap-1.5 font-display">
              <Clock className="w-3.5 h-3.5 text-bubblegum" />
              Protocol Deadlines
            </h3>
            <div className="space-y-2 text-[11px]">
              <div className="flex items-center justify-between text-ink-secondary">
                <span>Commit By:</span>
                <span className="font-mono text-ink">
                  {new Date(market.commit_deadline).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-ink-secondary">
                <span>Reveal By:</span>
                <span className="font-mono text-ink">
                  {new Date(market.reveal_deadline).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-ink-secondary">
                <span>Challenge By:</span>
                <span className="font-mono text-ink">
                  {new Date(market.challenge_deadline).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-ink-secondary pt-1.5 border-t border-hairline">
                <span>Reward Pool:</span>
                <span className="font-mono font-bold text-bubblegum-deep">
                  {market.reward_pool_credits} Credits
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

