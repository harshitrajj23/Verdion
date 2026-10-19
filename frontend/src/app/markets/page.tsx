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

  const [selectedMarketId, setSelectedMarketId] = useState<string>("mkt_gdpr_001");
  const [probInput, setProbInput] = useState<number>(70);
  const [nonceInput, setNonceInput] = useState<string>(
    "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [challengeReason, setChallengeReason] = useState("");

  const market = markets.find((m) => m.market_id === selectedMarketId) || markets[0];
  const relevantTxs = pendingTxs.filter(
    (tx) => tx.action.includes("Forecast") || tx.action.includes("Market") || tx.action.includes("Challenge")
  );

  if (!market) {
    return (
      <EmptyState
        icon={<TrendingUp className="w-7 h-7 text-cyan-500" />}
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

  // Determine which deadline to show based on market state
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
      ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
      : market.state === "VOID"
      ? "bg-slate-800 text-slate-400 border-slate-700"
      : market.state === "CHALLENGE"
      ? "bg-rose-950 text-rose-300 border-rose-500/40"
      : "bg-cyan-950 text-cyan-300 border-cyan-500/40";

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                §16.5
              </span>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">Prediction Market Protocol</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Commit-reveal probabilistic forecast aggregation over objectively resolvable evaluation outcomes.
            </p>
          </div>

          <div className="flex items-center gap-2 text-[11px] font-semibold text-amber-300 bg-amber-950/40 border border-amber-800/40 px-3 py-1.5 rounded-xl">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span>Probabilities are empirical event forecasts, not legal determinations (§16.5)</span>
          </div>
        </div>

        {/* Market Selector Tabs */}
        <div className="flex flex-wrap items-center gap-2">
          {markets.map((m) => (
            <button
              key={m.market_id}
              onClick={() => setSelectedMarketId(m.market_id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                selectedMarketId === m.market_id
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <span>{m.market_id}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                {m.state}
              </span>
            </button>
          ))}
        </div>
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
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold">
                  {market.market_id} • Case {market.case_id}
                </span>
                <h2 className="text-lg font-bold text-white mt-1">{market.question}</h2>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-bold border shrink-0 ${stateColor}`}>
                {market.state}
              </span>
            </div>

            {/* Outcome Definition & Resolution Rules (§10.2) */}
            <div className="space-y-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1">
                <span className="text-slate-400 font-semibold block">Precise Outcome Definition:</span>
                <p className="text-slate-200 leading-relaxed">{market.outcome_definition}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-0.5">
                  <span className="text-[10px] text-slate-400">Resolution Source:</span>
                  <p className="font-semibold text-slate-200">{market.resolution_source}</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 space-y-0.5">
                  <span className="text-[10px] text-slate-400">Authorized Evaluator:</span>
                  <p className="font-mono text-cyan-400 truncate">{market.evaluator_address}</p>
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
            <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Aggregated Belief Probability:</span>
                <span className="text-2xl font-extrabold font-mono text-cyan-400">
                  {(market.aggregate_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-3 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-400 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${market.aggregate_probability * 100}%` }}
                />
              </div>
              <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-1">
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3 text-cyan-400" />
                  Sample Size: <strong>N = {market.sample_size} Agents</strong>
                </span>
                <span>Disagreement Variance: <strong className="font-mono text-slate-200">{market.disagreement_variance}</strong></span>
                <span>Scoring Rule: <strong>Brier Proper Scoring</strong></span>
              </div>
            </div>

            {/* Revealed Forecasts Table */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Revealed Forecast Register ({market.revealed_forecasts.length})
              </h3>
              {market.revealed_forecasts.length === 0 ? (
                <EmptyState
                  icon={<Lock className="w-6 h-6 text-cyan-500" />}
                  title="No Forecasts Revealed Yet"
                  description="Forecasts will appear here once the reveal deadline is reached and agents disclose their committed probabilities."
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-semibold text-[10px] uppercase">
                        <th className="py-2.5 px-3">Agent</th>
                        <th className="py-2.5 px-3">Address</th>
                        <th className="py-2.5 px-3">Probability</th>
                        <th className="py-2.5 px-3">Evidence Digest</th>
                        <th className="py-2.5 px-3">Revealed Time</th>
                        <th className="py-2.5 px-3">Brier Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80">
                      {market.revealed_forecasts.map((f, i) => (
                        <tr key={i} className="hover:bg-slate-900/40 transition-colors">
                          <td className="py-2.5 px-3 font-semibold text-slate-200">{f.agent_id}</td>
                          <td className="py-2.5 px-3 font-mono text-[10px] text-cyan-400">
                            {f.agent_address.slice(0, 8)}...{f.agent_address.slice(-4)}
                          </td>
                          <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">
                            {(f.probability * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 px-3 font-mono text-[10px] text-slate-400">
                            {f.evidence_digest.slice(0, 10)}...{f.evidence_digest.slice(-6)}
                          </td>
                          <td className="py-2.5 px-3 text-[11px] text-slate-400">
                            {new Date(f.revealed_at).toLocaleTimeString()}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-[11px]">
                            {f.brier_score !== undefined ? (
                              <span className="text-emerald-400 font-bold">{f.brier_score.toFixed(4)}</span>
                            ) : (
                              <span className="text-slate-600">—</span>
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
              <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-semibold text-emerald-300">Market Settled</span>
                </div>
                <a
                  href={`https://sepolia.etherscan.io/tx/${market.settlement_tx}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                >
                  <span>{market.settlement_tx.slice(0, 14)}...{market.settlement_tx.slice(-8)}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right (1 col): Interactive Commit & Reveal Form (§10.4) */}
        <div className="space-y-6">
          {/* Commit / Reveal Interactive Form */}
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              <span>Commit-Reveal Terminal (§10.4)</span>
            </h3>

            {!isLiveChain && (
              <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-800/30 text-[10px] text-indigo-300 flex items-center gap-1.5">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>Sample mode — actions update local state only, not on-chain.</span>
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 font-semibold block mb-1">
                  Forecast Probability: <span className="text-cyan-400 font-mono font-bold">{probInput}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={probInput}
                  onChange={(e) => setProbInput(Number(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-600 mt-0.5">
                  <span>0% (NO)</span>
                  <span>100% (YES)</span>
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1 flex items-center justify-between">
                  <span>Secret Nonce (Entropy Salt):</span>
                  <button
                    onClick={() =>
                      setNonceInput(
                        "0x" + Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")
                      )
                    }
                    className="text-[10px] text-cyan-400 hover:text-cyan-300"
                  >
                    Generate New
                  </button>
                </label>
                <input
                  type="text"
                  value={nonceInput}
                  onChange={(e) => setNonceInput(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[10px] text-slate-300 focus:outline-none focus:border-cyan-500 transition-colors"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
                <span className="text-[10px] font-mono text-slate-400 block">Commitment Formula:</span>
                <p className="font-mono text-[9px] text-slate-400 leading-tight break-all">
                  keccak256(chainId, marketId, agent, prob, digest, nonce)
                </p>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 space-y-2">
                <button
                  onClick={handleCommit}
                  disabled={isSubmitting || market.state === "SETTLED" || market.state === "VOID"}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xs shadow-glow-cyan transition-all flex items-center justify-center gap-2"
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
                  className="w-full py-2.5 px-4 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 disabled:opacity-50 disabled:cursor-not-allowed font-bold text-xs transition-all flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner w-3.5 h-3.5 text-emerald-400" />
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
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Resolution & Settlement Console</span>
            </h3>

            {/* Challenge Status Display */}
            {market.challenge_status.is_challenged && (
              <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/30 text-xs space-y-1">
                <div className="flex items-center gap-1.5 text-rose-300 font-bold">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>Resolution Challenged</span>
                </div>
                {market.challenge_status.challenger && (
                  <div className="font-mono text-[10px] text-slate-400">
                    By: {market.challenge_status.challenger.slice(0, 10)}...
                  </div>
                )}
                {market.challenge_status.reason && (
                  <p className="text-[11px] text-slate-300">{market.challenge_status.reason}</p>
                )}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div className="space-y-1">
                <label className="text-slate-400 font-semibold block">Challenge Reason (if disputing):</label>
                <input
                  type="text"
                  placeholder="e.g. Incompatible EDPB interpretation"
                  value={challengeReason}
                  onChange={(e) => setChallengeReason(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500 transition-colors"
                />
              </div>

                <p className="text-[11px] text-amber-400/90 bg-amber-950/20 p-2 rounded-lg border border-amber-900/30">
                  Note: In this MVP, challenges are resolved by the protocol admin, who is also the evaluator.
                </p>

                <button
                  onClick={handleChallenge}
                  disabled={!challengeReason || isSubmitting || market.state === "SETTLED"}
                  className="w-full py-2 px-3 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 font-bold text-xs disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Submit Resolution Challenge (FR-046)
                </button>

              <button
                onClick={handleSettle}
                disabled={isSubmitting || market.state === "SETTLED"}
                className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Execute Proper Scoring Settlement (FR-048)
              </button>
            </div>
          </div>

          {/* Deadline Info Panel */}
          <div className="glass-panel p-5 rounded-3xl space-y-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              Protocol Deadlines
            </h3>
            <div className="space-y-2 text-[11px]">
              <div className="flex items-center justify-between text-slate-400">
                <span>Commit By:</span>
                <span className="font-mono text-slate-300">
                  {new Date(market.commit_deadline).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Reveal By:</span>
                <span className="font-mono text-slate-300">
                  {new Date(market.reveal_deadline).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>Challenge By:</span>
                <span className="font-mono text-slate-300">
                  {new Date(market.challenge_deadline).toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800/80">
                <span>Reward Pool:</span>
                <span className="font-mono font-bold text-emerald-400">
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
