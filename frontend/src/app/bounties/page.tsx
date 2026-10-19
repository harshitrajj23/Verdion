"use client";

import React, { useState, useMemo } from "react";
import { useStore } from "@/lib/store";
import { TransactionStatus } from "@/components/TransactionStatus";
import { DeadlineCountdown } from "@/components/DeadlineCountdown";
import { EmptyState } from "@/components/EmptyState";
import {
  Gift,
  Coins,
  ShieldCheck,
  Clock,
  AlertTriangle,
  FileCheck2,
  ExternalLink,
  PlusCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertCircle
} from "lucide-react";

export default function EvidenceBountiesPage() {
  const { bounties, submitBountyEvidence, settleBounty, userCredits, pendingTxs, isLiveChain } = useStore();
  const [selectedBountyId, setSelectedBountyId] = useState<string>("bounty_edpb_001");

  // Form states
  const [sourceTitle, setSourceTitle] = useState("");
  const [passageRef, setPassageRef] = useState("");
  const [quote, setQuote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const bounty = bounties.find((b) => b.bounty_id === selectedBountyId) || bounties[0];
  const relevantTxs = pendingTxs.filter(
    (tx) => tx.action.includes("Evidence") || tx.action.includes("Bounty")
  );

  // Compute weighted rubric score
  const weightedScore = useMemo(() => {
    if (!bounty) return 0;
    return bounty.acceptance_rubric.reduce((acc, r) => {
      return acc + (r.score || 0) * r.weight;
    }, 0);
  }, [bounty]);

  if (!bounty) {
    return (
      <EmptyState
        icon={<Gift className="w-7 h-7 text-amber-500" />}
        title="No Evidence Bounties Available"
        description="No bounties have been created for this case yet."
      />
    );
  }

  const handleSubmitEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceTitle || !passageRef || !quote) return;
    setIsSubmitting(true);
    try {
      await submitBountyEvidence(bounty.bounty_id, sourceTitle, passageRef, quote);
      setSourceTitle("");
      setPassageRef("");
      setQuote("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSettle = async () => {
    setIsSubmitting(true);
    try {
      await settleBounty(bounty.bounty_id);
    } finally {
      setIsSubmitting(false);
    }
  };

  const stateColor =
    bounty.state === "SETTLED" || bounty.state === "AWARDED"
      ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
      : bounty.state === "CHALLENGE"
      ? "bg-rose-950 text-rose-300 border-rose-500/40"
      : bounty.state === "REJECTED" || bounty.state === "CANCELLED"
      ? "bg-slate-800 text-slate-400 border-slate-700"
      : "bg-amber-950 text-amber-300 border-amber-500/40";

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                §16.6
              </span>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">Evidence Bounty Protocol</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Directing economic incentives toward specific legal uncertainties using simulated credits and standardized acceptance rubrics.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
              <Coins className="w-4 h-4 text-emerald-400" />
              <span>Your Balance: <strong className="font-mono text-emerald-300">{userCredits}</strong> Credits</span>
            </div>
          </div>
        </div>

        {/* Bounty Selector */}
        <div className="flex flex-wrap items-center gap-2">
          {bounties.map((b) => (
            <button
              key={b.bounty_id}
              onClick={() => setSelectedBountyId(b.bounty_id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all ${
                selectedBountyId === b.bounty_id
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-glow"
                  : "bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              <span>{b.bounty_id}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                {b.state}
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

      {/* Main Bounty Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2 cols): Bounty Details & Rubric */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-3xl space-y-5">
            <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono text-amber-400 uppercase font-bold">
                    {bounty.bounty_id} • Case {bounty.case_id}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${stateColor}`}>
                    {bounty.state}
                  </span>
                </div>
                <h2 className="text-base sm:text-lg font-bold text-white">
                  Target Research Uncertainty:
                </h2>
                <p className="text-xs text-slate-200 mt-1 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  {bounty.question}
                </p>
              </div>
              <div className="text-right shrink-0">
                <span className="text-lg font-extrabold font-mono text-emerald-400">
                  +{bounty.reward_credits} Credits
                </span>
                <span className="block text-[10px] uppercase font-bold text-slate-400 mt-0.5">
                  Simulated Reward (FR-041)
                </span>
              </div>
            </div>

            {/* Challenge Deadline Countdown */}
            {bounty.challenge_deadline && bounty.state !== "SETTLED" && (
              <DeadlineCountdown
                deadline={bounty.challenge_deadline}
                label="Challenge Window Deadline"
                accent="rose"
              />
            )}

            {/* Published Acceptance Rubric (§11.3) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />
                  <span>Published Acceptance Rubric Criteria (§11.3)</span>
                </h3>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  Weighted Score: {(weightedScore * 100).toFixed(1)}%
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {bounty.acceptance_rubric.map((r, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{r.criterion}</span>
                      {r.score && (
                        <span className="font-mono text-emerald-400 font-bold">
                          {(r.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                        style={{ width: `${(r.score || 0) * 100}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-slate-500">
                      Weight: {(r.weight * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Submissions Register */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Evidence Submissions ({bounty.submissions.length})
              </h3>
              {bounty.submissions.length === 0 ? (
                <EmptyState
                  icon={<PlusCircle className="w-6 h-6 text-amber-500" />}
                  title="No Submissions Yet"
                  description="Submit authoritative evidence references to earn the bounty reward."
                />
              ) : (
                <div className="space-y-3">
                  {bounty.submissions.map((sub) => (
                    <div
                      key={sub.submission_id}
                      className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <span className="text-xs font-bold text-white">{sub.source_title}</span>
                          <span className="block text-[11px] text-cyan-400 font-mono">
                            {sub.passage_reference}
                          </span>
                        </div>
                        {sub.is_accepted === true ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> ACCEPTED
                          </span>
                        ) : sub.is_accepted === false ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-500/40 flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> REJECTED
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-500/40">
                            PENDING REVIEW
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-300 italic bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                        &ldquo;{sub.quote}&rdquo;
                      </p>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px] font-mono text-slate-400 pt-1">
                        <div>Digest: <span className="text-cyan-400">{sub.evidence_digest.slice(0, 16)}...</span></div>
                        <div>Contributor: <span className="text-slate-300">{sub.contributor.slice(0, 12)}...</span></div>
                        <div>Submitted: <span className="text-slate-300">{new Date(sub.submitted_at).toLocaleDateString()}</span></div>
                      </div>

                      {sub.reviewer_reason && (
                        <div className="p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-[11px] text-emerald-200">
                          <strong>Reviewer Rationale:</strong> {sub.reviewer_reason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Settlement Tx */}
            {bounty.settlement_tx && (
              <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/30 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-semibold text-emerald-300">Bounty Settled</span>
                </div>
                <a
                  href={`https://sepolia.etherscan.io/tx/${bounty.settlement_tx}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                >
                  <span>{bounty.settlement_tx.slice(0, 14)}...{bounty.settlement_tx.slice(-8)}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right (1 col): Submission Form & Settle Action */}
        <div className="space-y-6">
          {/* Submit Evidence Form */}
          <div className="glass-panel p-6 rounded-3xl space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <PlusCircle className="w-4 h-4 text-amber-400" />
              <span>Submit Evidence Reference</span>
            </h3>

            {!isLiveChain && (
              <div className="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-800/30 text-[10px] text-indigo-300 flex items-center gap-1.5">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>Sample mode — submissions update local state only.</span>
              </div>
            )}

            <form onSubmit={handleSubmitEvidence} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 font-semibold block mb-1">Source Title:</label>
                <input
                  type="text"
                  placeholder="e.g. CJEU Case C-300/21 or EDPB Statement"
                  value={sourceTitle}
                  onChange={(e) => setSourceTitle(e.target.value)}
                  required
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 transition-colors"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Passage Reference:</label>
                <input
                  type="text"
                  placeholder="e.g. Paragraph 42 or Section 3.1"
                  value={passageRef}
                  onChange={(e) => setPassageRef(e.target.value)}
                  required
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 transition-colors"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold block mb-1">Exact Passage Text Quote:</label>
                <textarea
                  rows={3}
                  placeholder="Paste exact authoritative quote..."
                  value={quote}
                  onChange={(e) => setQuote(e.target.value)}
                  required
                  className="w-full p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-amber-500 resize-none transition-colors"
                />
              </div>

              <div className="text-[10px] text-slate-500 leading-tight">
                Canonical Keccak256 digest will be generated deterministically and registered on EvidenceBounty contract (FR-026, FR-042).
              </div>

              <button
                type="submit"
                disabled={isSubmitting || bounty.state === "SETTLED"}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-emerald-600 hover:from-amber-500 hover:to-emerald-500 text-white font-bold text-xs shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner w-3.5 h-3.5 text-white" />
                    Submitting...
                  </>
                ) : (
                  "Submit to Bounty Contract"
                )}
              </button>
            </form>
          </div>

          {/* Settle Action */}
          <div className="glass-panel p-6 rounded-3xl space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Authorized Bounty Settlement</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Once the 24-hour challenge window elapses without dispute, the evaluator settles the bounty idempotently.
            </p>
            <button
              onClick={handleSettle}
              disabled={isSubmitting || bounty.state === "SETTLED"}
              className="w-full py-2.5 px-4 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Execute Bounty Settlement (FR-050)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
