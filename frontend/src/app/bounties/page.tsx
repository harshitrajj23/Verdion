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
  const [selectedBountyId, setSelectedBountyId] = useState<string>("");

  // Form states
  const [sourceTitle, setSourceTitle] = useState("");
  const [passageRef, setPassageRef] = useState("");
  const [quote, setQuote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeBountyId = selectedBountyId && bounties.some((b) => b.bounty_id === selectedBountyId)
    ? selectedBountyId
    : (bounties[0]?.bounty_id || "");
  const bounty = bounties.find((b) => b.bounty_id === activeBountyId) || bounties[0];
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
        icon={<Gift className="w-7 h-7 text-lavender-600" />}
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
      ? "bg-lavender-100 text-lavender-800 border-lavender-300"
      : bounty.state === "CHALLENGE"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : bounty.state === "REJECTED" || bounty.state === "CANCELLED"
      ? "bg-cream-200 text-ink-muted border-cream-300"
      : "bg-amber-50 text-amber-800 border-amber-200";

  return (
    <div className="space-y-8 animate-fade-in-up">
      {/* ── Apple Header Card ── */}
      <div className="apple-card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline pb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-bubblegum-soft text-bubblegum-deep border border-hairline">
                §16.6
              </span>
              <h1 className="text-2xl sm:text-3xl font-semibold text-ink tracking-tight font-display">
                Evidence Bounty Protocol
              </h1>
            </div>
            <p className="text-xs text-muted mt-1">
              Directing economic incentives toward specific legal uncertainties using simulated credits and standardized acceptance rubrics.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-cloud border border-hairline text-xs">
              <Coins className="w-4 h-4 text-bubblegum" />
              <span className="text-muted">Balance: <strong className="font-mono text-bubblegum-deep font-semibold">{userCredits}</strong> Credits</span>
            </div>
          </div>
        </div>

        {/* Bounty Selector: Pill Bar */}
        <div className="inline-flex p-1 rounded-full bg-cloud border border-hairline max-w-full overflow-x-auto scrollbar-none">
          {bounties.map((b) => (
            <button
              key={b.bounty_id}
              onClick={() => setSelectedBountyId(b.bounty_id)}
              className={`px-4 py-1.5 rounded-full text-xs font-medium flex items-center gap-2 transition-all duration-150 active:scale-[0.97] ${
                selectedBountyId === b.bounty_id
                  ? "bg-bubblegum text-white shadow-soft font-semibold"
                  : "text-muted hover:text-ink hover:bg-bubblegum-soft/40"
              }`}
            >
              <span>{b.bounty_id}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cloud text-muted font-mono">
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
          <div className="apple-card space-y-5">
            <div className="flex items-start justify-between gap-3 border-b border-cream-200 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] font-mono text-lavender-700 uppercase font-semibold">
                    {bounty.bounty_id} • Case {bounty.case_id}
                  </span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${stateColor}`}>
                    {bounty.state}
                  </span>
                </div>
                <h2 className="text-xs font-semibold text-ink-muted uppercase tracking-wider font-appleDisplay">
                  Target Research Uncertainty:
                </h2>
                <div className="text-sm font-normal text-ink mt-1.5 leading-relaxed bg-cream-50 p-4 rounded-[14px] border border-cream-200">
                  {bounty.question}
                </div>
              </div>
              <div className="text-right shrink-0">
                <span className="text-xl font-bold font-mono text-lavender-700">
                  +{bounty.reward_credits} Credits
                </span>
                <span className="block text-[10px] uppercase font-semibold text-ink-muted mt-0.5">
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
                <h3 className="text-xs font-semibold text-ink-muted uppercase tracking-wider flex items-center gap-1.5 font-appleDisplay">
                  <FileCheck2 className="w-4 h-4 text-lavender-600" />
                  <span>Published Acceptance Rubric Criteria (§11.3)</span>
                </h3>
                <span className="text-xs font-mono font-bold text-lavender-700">
                  Weighted Score: {(weightedScore * 100).toFixed(1)}%
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {bounty.acceptance_rubric.map((r, i) => (
                  <div key={i} className="p-3.5 rounded-[12px] bg-cream-50 border border-cream-200 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-ink">{r.criterion}</span>
                      {r.score && (
                        <span className="font-mono text-lavender-700 font-bold">
                          {(r.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-cream-200 overflow-hidden">
                      <div
                        className="h-full bg-lavender-600 rounded-full transition-all duration-500"
                        style={{ width: `${(r.score || 0) * 100}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-ink-muted font-medium">
                      Weight: {(r.weight * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Submissions Register */}
            <div className="space-y-3 pt-2">
              <h3 className="text-xs font-semibold text-ink-muted uppercase tracking-wider font-appleDisplay">
                Evidence Submissions ({bounty.submissions.length})
              </h3>
              {bounty.submissions.length === 0 ? (
                <EmptyState
                  icon={<PlusCircle className="w-6 h-6 text-lavender-600" />}
                  title="No Submissions Yet"
                  description="Submit authoritative evidence references to earn the bounty reward."
                />
              ) : (
                <div className="space-y-3">
                  {bounty.submissions.map((sub) => (
                    <div
                      key={sub.submission_id}
                      className="p-4 rounded-[14px] bg-cream-50 border border-cream-200 space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <span className="text-xs font-semibold text-ink">{sub.source_title}</span>
                          <span className="block text-[11px] text-lavender-700 font-mono mt-0.5">
                            {sub.passage_reference}
                          </span>
                        </div>
                        {sub.is_accepted === true ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-100 text-lavender-800 border border-lavender-200 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3 text-lavender-600" /> ACCEPTED
                          </span>
                        ) : sub.is_accepted === false ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
                            <XCircle className="w-3 h-3 text-rose-600" /> REJECTED
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                            PENDING REVIEW
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-ink-secondary italic bg-white p-3 rounded-[10px] border border-cream-200 leading-relaxed">
                        &ldquo;{sub.quote}&rdquo;
                      </p>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px] font-mono text-ink-muted pt-1">
                        <div>Digest: <span className="text-lavender-700">{sub.evidence_digest.slice(0, 16)}...</span></div>
                        <div>Contributor: <span className="text-ink">{sub.contributor.slice(0, 12)}...</span></div>
                        <div>Submitted: <span className="text-ink">{new Date(sub.submitted_at).toLocaleDateString()}</span></div>
                      </div>

                      {sub.reviewer_reason && (
                        <div className="p-3 rounded-[10px] bg-lavender-50 border border-lavender-200 text-xs text-lavender-900 leading-relaxed">
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
              <div className="p-3.5 rounded-[12px] bg-lavender-50 border border-lavender-200 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-lavender-600" />
                  <span className="font-semibold text-lavender-800">Bounty Settled</span>
                </div>
                <a
                  href={`https://sepolia.etherscan.io/tx/${bounty.settlement_tx}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] text-lavender-700 hover:underline flex items-center gap-1 font-medium"
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
          <div className="apple-card space-y-4">
            <h3 className="text-base font-semibold text-ink flex items-center gap-2 font-appleDisplay">
              <PlusCircle className="w-4 h-4 text-lavender-600" />
              <span>Submit Evidence Reference</span>
            </h3>

            {!isLiveChain && (
              <div className="p-2.5 rounded-[10px] bg-cream-200/80 border border-cream-300 text-[11px] text-ink-secondary flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-lavender-600 shrink-0" />
                <span>Sample mode — submissions update local state only.</span>
              </div>
            )}

            <form onSubmit={handleSubmitEvidence} className="space-y-3.5 text-xs">
              <div>
                <label className="text-ink-secondary font-medium block mb-1">Source Title:</label>
                <input
                  type="text"
                  placeholder="e.g. CJEU Case C-300/21 or EDPB Statement"
                  value={sourceTitle}
                  onChange={(e) => setSourceTitle(e.target.value)}
                  required
                  className="w-full p-2.5 rounded-[10px] bg-cream-50 border border-cream-300 text-ink focus:outline-none focus:border-lavender-400 transition-colors"
                />
              </div>

              <div>
                <label className="text-ink-secondary font-medium block mb-1">Passage Reference:</label>
                <input
                  type="text"
                  placeholder="e.g. Paragraph 42 or Section 3.1"
                  value={passageRef}
                  onChange={(e) => setPassageRef(e.target.value)}
                  required
                  className="w-full p-2.5 rounded-[10px] bg-cream-50 border border-cream-300 text-ink focus:outline-none focus:border-lavender-400 transition-colors"
                />
              </div>

              <div>
                <label className="text-ink-secondary font-medium block mb-1">Exact Passage Text Quote:</label>
                <textarea
                  rows={3}
                  placeholder="Paste exact authoritative quote..."
                  value={quote}
                  onChange={(e) => setQuote(e.target.value)}
                  required
                  className="w-full p-2.5 rounded-[10px] bg-cream-50 border border-cream-300 text-ink focus:outline-none focus:border-lavender-400 resize-none transition-colors"
                />
              </div>

              <div className="text-[11px] text-ink-muted leading-tight">
                Canonical Keccak256 digest will be generated deterministically and registered on EvidenceBounty contract (FR-026, FR-042).
              </div>

              <button
                type="submit"
                disabled={isSubmitting || bounty.state === "SETTLED"}
                className="apple-btn-primary w-full py-2.5 justify-center disabled:opacity-40 disabled:cursor-not-allowed"
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
          <div className="apple-card space-y-3">
            <h3 className="text-base font-semibold text-ink flex items-center gap-2 font-appleDisplay">
              <ShieldCheck className="w-4 h-4 text-lavender-600" />
              <span>Authorized Bounty Settlement</span>
            </h3>
            <p className="text-xs text-ink-secondary leading-relaxed">
              Once the 24-hour challenge window elapses without dispute, the evaluator settles the bounty idempotently.
            </p>
            <button
              onClick={handleSettle}
              disabled={isSubmitting || bounty.state === "SETTLED"}
              className="apple-btn-secondary w-full py-2.5 justify-center disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Execute Bounty Settlement (FR-050)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

