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

  const [selectedMarketId, setSelectedMarketId] = useState<string>("0x28ae...5b3e (Sepolia Lifecycle)");
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
      ? "bg-lavender-100 text-lavender-800 border-lavender-300"
      : market.state === "VOID"
      ? "bg-cream-200 text-ink-muted border-cream-300"
      : market.state === "CHALLENGE"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : "bg-lavender-50 text-lavender-700 border-lavender-200";

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* ── Apple Header Card ── */}
      <div className="apple-card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200">
                §16.5
              </span>
              <h1 className="text-2xl sm:text-3xl font-semibold text-ink tracking-tight font-appleDisplay">
                Prediction Market Protocol
              </h1>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              Commit-reveal probabilistic forecast aggregation over objectively resolvable evaluation outcomes.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-medium text-amber-900 bg-amber-50 border border-amber-200 px-3.5 py-1.5 rounded-full">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>Empirical event forecasts, not final legal determinations</span>
          </div>
        </div>

        {/* Market Selector Tabs */}
        <div className="inline-flex p-1 rounded-full bg-cream-200 border border-cream-300 max-w-full overflow-x-auto scrollbar-none">
          {markets.map((m) => (
            <button
              key={m.market_id}
              onClick={() => setSelectedMarketId(m.market_id)}
              className={`px-4 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 transition-all duration-150 active:scale-[0.97] ${
                selectedMarketId === m.market_id
                  ? "bg-white text-ink shadow-sm border border-cream-300/60"
                  : "text-ink-secondary hover:text-ink hover:bg-cream-100/60"
              }`}
            >
              <span>{m.market_id}</span>
              {m.is_recorded_sepolia ? (
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold border border-emerald-200">
                  On-Chain
                </span>
              ) : (
                <span className="text-[9px] px-2 py-0.5 rounded-full bg-cream-100 text-ink-muted font-mono">
                  Sample
                </span>
              )}
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cream-100 text-ink-muted font-mono">
                {m.state}
              </span>
            </button>
          ))}
        </div>

        {/* Protocol Disclosures & Architecture Transparency */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-cream-200">
          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 space-y-1 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-lavender-700">
              <Users className="w-3.5 h-3.5" />
              <span>Demonstration Architecture Disclosure</span>
            </div>
            <p className="text-ink-secondary leading-relaxed text-[11px]">
              The recorded Sepolia on-chain lifecycle (<span className="font-mono text-ink">0x28ae...5b3e</span>) was executed with a single deployer account (<span className="font-mono text-ink">0x3486...2888</span>) acting as both agent and evaluator. Multi-agent panels (<span className="font-semibold text-ink">N = 3</span>) represent simulated benchmark scenarios to demonstrate protocol aggregation.
            </p>
          </div>

          <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 space-y-1 text-xs">
            <div className="flex items-center gap-1.5 font-semibold text-lavender-700">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Limitation 3: Event-Definition Mismatch</span>
            </div>
            <p className="text-ink-secondary leading-relaxed text-[11px]">
              Upstream ML forecasters predict general GDPR/EU AI Act liability outcomes, whereas <span className="font-mono text-ink">PredictionMarket</span> resolves on specific evaluator rubric gap findings. Operational deployment requires alignment between question syntax and on-chain rubric criteria.
            </p>
          </div>
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
          <div className="apple-card space-y-5">
            <div className="flex items-start justify-between gap-3 border-b border-cream-200 pb-4">
              <div>
                <span className="text-[11px] font-mono text-lavender-700 uppercase font-semibold">
                  {market.market_id} • Case {market.case_id}
                </span>
                <h2 className="text-xl font-semibold text-ink mt-1 font-appleDisplay">{market.question}</h2>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border shrink-0 ${stateColor}`}>
                {market.state}
              </span>
            </div>

            {/* Outcome Definition & Resolution Rules (§10.2) */}
            <div className="space-y-3 text-xs">
              <div className="p-4 rounded-[14px] bg-cream-200/50 border border-cream-300 space-y-1">
                <span className="text-ink-muted font-semibold block uppercase tracking-wider text-[10px]">
                  Precise Outcome Definition:
                </span>
                <p className="text-ink leading-relaxed">{market.outcome_definition}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-0.5">
                  <span className="text-[10px] text-ink-muted font-medium">Resolution Source:</span>
                  <p className="font-semibold text-ink">{market.resolution_source}</p>
                </div>
                <div className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-300 space-y-0.5">
                  <span className="text-[10px] text-ink-muted font-medium">Authorized Evaluator:</span>
                  <p className="font-mono text-lavender-700 truncate">{market.evaluator_address}</p>
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
            <div className="p-5 rounded-[16px] bg-cream-50 border border-cream-300 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-ink-secondary">Aggregated Belief Probability:</span>
                <span className="text-3xl font-bold font-mono text-lavender-700">
                  {(market.aggregate_probability * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-cream-200 overflow-hidden border border-cream-300">
                <div
                  className="h-full bg-lavender-600 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${market.aggregate_probability * 100}%` }}
                />
              </div>
              <div className="flex flex-wrap items-center justify-between text-xs text-ink-muted pt-1">
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-lavender-600" />
                  Sample Size: <strong className="text-ink font-medium">N = {market.sample_size} {market.is_recorded_sepolia ? "Agent (Single Deployer Demo)" : "Agents (Simulated)"}</strong>
                </span>
                <span>Disagreement Variance: <strong className="font-mono text-ink font-medium">{market.disagreement_variance}</strong></span>
                <span>Rule: <strong className="text-ink font-medium">Brier Proper Scoring</strong></span>
              </div>
            </div>

            {/* Revealed Forecasts Table */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold text-ink-muted uppercase tracking-wider font-appleDisplay">
                Revealed Forecast Register ({market.revealed_forecasts.length})
              </h3>
              {market.revealed_forecasts.length === 0 ? (
                <EmptyState
                  icon={<Lock className="w-6 h-6 text-lavender-600" />}
                  title="No Forecasts Revealed Yet"
                  description="Forecasts will appear here once the reveal deadline is reached and agents disclose their committed probabilities."
                />
              ) : (
                <div className="overflow-x-auto rounded-[14px] border border-cream-200">
                  <table className="w-full text-left text-xs border-collapse bg-white">
                    <thead>
                      <tr className="border-b border-cream-200 bg-cream-50/70 text-ink-muted font-semibold text-[10px] uppercase">
                        <th className="py-3 px-3.5">Agent</th>
                        <th className="py-3 px-3.5">Address</th>
                        <th className="py-3 px-3.5">Probability</th>
                        <th className="py-3 px-3.5">Evidence Digest</th>
                        <th className="py-3 px-3.5">Revealed Time</th>
                        <th className="py-3 px-3.5">Brier Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-cream-200">
                      {market.revealed_forecasts.map((f, i) => (
                        <tr key={i} className="hover:bg-cream-50/60 transition-colors">
                          <td className="py-3 px-3.5 font-semibold text-ink">{f.agent_id}</td>
                          <td className="py-3 px-3.5 font-mono text-[10px] text-lavender-700">
                            {f.agent_address.slice(0, 8)}...{f.agent_address.slice(-4)}
                          </td>
                          <td className="py-3 px-3.5 font-mono font-bold text-lavender-700 text-sm">
                            {(f.probability * 100).toFixed(1)}%
                          </td>
                          <td className="py-3 px-3.5 font-mono text-[10px] text-ink-muted">
                            {f.evidence_digest.slice(0, 10)}...{f.evidence_digest.slice(-6)}
                          </td>
                          <td className="py-3 px-3.5 text-[11px] text-ink-secondary">
                            {new Date(f.revealed_at).toLocaleTimeString()}
                          </td>
                          <td className="py-3 px-3.5 font-mono text-[11px]">
                            {f.brier_score !== undefined ? (
                              <span className="text-lavender-700 font-semibold">{f.brier_score.toFixed(4)}</span>
                            ) : (
                              <span className="text-ink-muted">—</span>
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
              <div className="p-3.5 rounded-[12px] bg-lavender-50 border border-lavender-200 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-lavender-600" />
                  <span className="font-semibold text-lavender-800">
                    {market.is_recorded_sepolia ? "Market Settled On-Chain (Sepolia)" : "Market Settled (Simulated Benchmark)"}
                  </span>
                </div>
                {market.is_recorded_sepolia ? (
                  <a
                    href={`https://sepolia.etherscan.io/tx/${market.settlement_tx}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-[11px] text-lavender-700 hover:underline flex items-center gap-1 font-medium"
                  >
                    <span>{market.settlement_tx.slice(0, 14)}...{market.settlement_tx.slice(-8)}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="font-mono text-[11px] text-ink-muted">
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
          <div className="apple-card space-y-4">
            <h3 className="text-base font-semibold text-ink flex items-center gap-2 font-appleDisplay">
              <Lock className="w-4 h-4 text-lavender-600" />
              <span>Commit-Reveal Terminal (§10.4)</span>
            </h3>

            {!isLiveChain && (
              <div className="p-2.5 rounded-[10px] bg-cream-200/80 border border-cream-300 text-[11px] text-ink-secondary flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-lavender-600 shrink-0" />
                <span>Sample mode — actions update local store only.</span>
              </div>
            )}

            <div className="space-y-3.5 text-xs">
              <div>
                <label className="text-ink-secondary font-medium block mb-1">
                  Forecast Probability: <span className="text-lavender-700 font-mono font-bold text-sm">{probInput}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={probInput}
                  onChange={(e) => setProbInput(Number(e.target.value))}
                  className="w-full accent-lavender-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-ink-muted mt-0.5">
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
                    className="text-[11px] text-lavender-700 hover:underline font-medium"
                  >
                    Generate New
                  </button>
                </label>
                <input
                  type="text"
                  value={nonceInput}
                  onChange={(e) => setNonceInput(e.target.value)}
                  className="w-full p-2.5 rounded-[10px] bg-cream-50 border border-cream-300 font-mono text-[10px] text-ink focus:outline-none focus:border-lavender-400 transition-colors"
                />
              </div>

              <div className="p-3 rounded-[10px] bg-cream-200/60 border border-cream-300 space-y-1">
                <span className="text-[10px] font-mono text-ink-muted block font-semibold">Commitment Formula:</span>
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
                  className="apple-btn-secondary w-full py-2.5 justify-center text-lavender-800 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner w-3.5 h-3.5 text-lavender-600" />
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
          <div className="apple-card space-y-4">
            <h3 className="text-base font-semibold text-ink flex items-center gap-2 font-appleDisplay">
              <ShieldCheck className="w-4 h-4 text-lavender-600" />
              <span>Resolution & Settlement Console</span>
            </h3>

            {market.challenge_status.is_challenged && (
              <div className="p-3 rounded-[10px] bg-rose-50 border border-rose-200 text-xs space-y-1">
                <div className="flex items-center gap-1.5 text-rose-800 font-semibold">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>Resolution Challenged</span>
                </div>
                {market.challenge_status.challenger && (
                  <div className="font-mono text-[10px] text-ink-muted">
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
                  className="w-full p-2.5 rounded-[10px] bg-cream-50 border border-cream-300 text-xs text-ink focus:outline-none focus:border-rose-400 transition-colors"
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
          <div className="apple-card space-y-3">
            <h3 className="text-xs font-semibold text-ink-muted uppercase tracking-wider flex items-center gap-1.5 font-appleDisplay">
              <Clock className="w-3.5 h-3.5 text-lavender-600" />
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
              <div className="flex items-center justify-between text-ink-secondary pt-1.5 border-t border-cream-200">
                <span>Reward Pool:</span>
                <span className="font-mono font-bold text-lavender-700">
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

