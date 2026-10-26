"use client";

import React from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import {
  Briefcase,
  TrendingUp,
  Gift,
  Coins,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  Database,
  Radio,
  FileCheck,
  Scale,
  Cpu
} from "lucide-react";

export default function DashboardPage() {
  const { currentCase, markets, bounties, auditRecords, isLiveChain, userCredits } = useStore();

  const activeMarket = markets[0];
  const activeBounty = bounties[0];
  const settlements = auditRecords.filter(
    (a) => a.event_type === "SETTLEMENT_EXECUTED" || a.event_type === "BOUNTY_SETTLED"
  );

  return (
    <div className="space-y-10 animate-fade-in-up">
      {/* ── Apple Hero Tile: Dark Obsidian Tile (design.md §product-tile-dark) ── */}
      <section className="relative overflow-hidden rounded-[24px] bg-tile-dark text-cream-100 p-8 sm:p-12 border border-tile-border shadow-apple-hover">
        <div className="relative z-10 max-w-3xl space-y-5">
          {/* Top Category Tag & Mode Indicator */}
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-lavender-500/20 text-lavender-300 border border-lavender-500/30">
              <Sparkles className="w-3.5 h-3.5 text-lavender-300" />
              <span>Decentralized Legal Intelligence Protocol</span>
            </span>

            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium border ${
                isLiveChain
                  ? "bg-lavender-900/60 text-lavender-200 border-lavender-500/40"
                  : "bg-cream-200/20 text-cream-200 border-cream-400/30"
              }`}
            >
              {isLiveChain ? (
                <>
                  <Radio className="w-3 h-3 text-lavender-300" />
                  <span>Sepolia Testnet Live</span>
                </>
              ) : (
                <>
                  <Database className="w-3 h-3 text-cream-300" />
                  <span>Curated Benchmark Sample</span>
                </>
              )}
            </span>
          </div>

          {/* Apple Display Headline (design.md §display-lg: 40px, 600 weight, -0.28px tracking) */}
          <div className="space-y-2">
            <h1 className="text-3xl sm:text-5xl font-semibold tracking-apple-tight text-white leading-[1.08] font-appleDisplay">
              Evidence-Grounded Legal Risk Forecasting.
            </h1>
            <p className="text-base sm:text-lg text-cream-300 font-normal leading-relaxed max-w-2xl font-appleText">
              Coordinating autonomous multi-agent swarms, prediction markets, and evidence bounties.
              Cryptographically verified on-chain via commit-reveal proper scoring.
            </p>
          </div>

          {/* Action CTAs: Apple Pill CTAs (§button-primary & §button-secondary-pill) */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href="/cases"
              className="apple-btn-primary"
            >
              <span>Explore Case Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/markets"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full text-[15px] font-medium text-cream-100 bg-tile-dark2 hover:bg-tile-dark3 border border-tile-border transition-all active:scale-[0.97]"
            >
              <TrendingUp className="w-4 h-4 text-lavender-300" />
              <span>Prediction Markets</span>
            </Link>
          </div>

          {/* Metadata Footprint Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-4 border-t border-tile-border/60 text-xs text-cream-400">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-tile-dark2 border border-tile-border/80">
              <span className="w-1.5 h-1.5 rounded-full bg-lavender-400" />
              <span>Jurisdiction: <strong className="text-cream-200">European Union</strong></span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-tile-dark2 border border-tile-border/80">
              <span className="w-1.5 h-1.5 rounded-full bg-lavender-300" />
              <span>Corpus Digest: <strong className="font-mono text-cream-200">0x8fa12b...</strong></span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-tile-dark2 border border-tile-border/80">
              <span className="w-1.5 h-1.5 rounded-full bg-lavender-400" />
              <span>Swarm Nodes: <strong className="text-cream-200">6 Specialized Agents</strong></span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Protocol Key Metrics: Apple Store Utility Cards (design.md §store-utility-card) ── */}
      <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="apple-card space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-ink-secondary">
            <span>Active Cases</span>
            <Briefcase className="w-4 h-4 text-lavender-600" />
          </div>
          <div className="text-3xl font-semibold tracking-tight text-ink font-appleDisplay">1</div>
          <span className="inline-block text-[11px] font-medium text-lavender-700 bg-lavender-100 px-2 py-0.5 rounded-full">
            Scope v{currentCase.scope_version} Frozen
          </span>
        </div>

        <div className="apple-card space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-ink-secondary">
            <span>Prediction Markets</span>
            <TrendingUp className="w-4 h-4 text-lavender-600" />
          </div>
          <div className="text-3xl font-semibold tracking-tight text-ink font-appleDisplay">{markets.length}</div>
          <span className="inline-block text-[11px] font-medium text-lavender-700 bg-lavender-100 px-2 py-0.5 rounded-full">
            1 Reveal, 1 Settled
          </span>
        </div>

        <div className="apple-card space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-ink-secondary">
            <span>Evidence Bounties</span>
            <Gift className="w-4 h-4 text-lavender-600" />
          </div>
          <div className="text-3xl font-semibold tracking-tight text-ink font-appleDisplay">{bounties.length}</div>
          <span className="inline-block text-[11px] font-medium text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full">
            Challenge Window
          </span>
        </div>

        <div className="apple-card space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-ink-secondary">
            <span>Brier Score</span>
            <Coins className="w-4 h-4 text-lavender-600" />
          </div>
          <div className="text-3xl font-semibold tracking-tight text-ink font-mono">0.0210</div>
          <span className="inline-block text-[11px] font-medium text-lavender-700 bg-lavender-100 px-2 py-0.5 rounded-full">
            97.9% Calibrated
          </span>
        </div>

        <div className="apple-card space-y-2 col-span-2 sm:col-span-1">
          <div className="flex items-center justify-between text-xs font-medium text-ink-secondary">
            <span>Settlements</span>
            <FileCheck className="w-4 h-4 text-lavender-600" />
          </div>
          <div className="text-3xl font-semibold tracking-tight text-ink font-mono">{settlements.length}</div>
          <span className="inline-block text-[11px] font-medium text-lavender-700 bg-lavender-100 px-2 py-0.5 rounded-full">
            On-Chain Verified
          </span>
        </div>
      </section>

      {/* ── Main Workspace Grid: Case Spotlight + Quick Actions ── */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2 cols): Active Case Spotlight */}
        <div className="lg:col-span-2 apple-card space-y-6">
          <div className="flex items-start justify-between gap-3 border-b border-cream-200 pb-5">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200 uppercase">
                  {currentCase.id}
                </span>
                <span className="text-xs text-ink-muted">Scope Version {currentCase.scope_version}</span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-cream-200 text-ink-secondary">
                  {isLiveChain ? "Live Chain Scope" : "Curated Dataset"}
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-semibold text-ink mt-2 tracking-tight font-appleDisplay">
                {currentCase.title}
              </h2>
            </div>
            <Link
              href="/cases"
              className="apple-btn-secondary text-xs px-3.5 py-1.5 shrink-0"
            >
              <span>Open Case</span>
              <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
            </Link>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Investigative Question:
            </span>
            <div className="p-4 rounded-[14px] bg-cream-200/60 border border-cream-300 text-[15px] text-ink leading-relaxed font-normal">
              {currentCase.question}
            </div>
          </div>

          {/* Missing Facts Alert */}
          {currentCase.missing_facts.length > 0 && (
            <div className="p-4 rounded-[14px] bg-amber-50 border border-amber-200 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-amber-900">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Missing Material Facts Identified (FR-002):</span>
              </div>
              <ul className="space-y-1 text-xs text-amber-800 pl-6 list-disc">
                {currentCase.missing_facts.map((mf, idx) => (
                  <li key={idx}>{mf}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Case Facts Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300">
              <span className="text-[11px] text-ink-muted block font-medium">Processing Purpose:</span>
              <span className="text-xs font-semibold text-ink truncate block mt-0.5">
                {currentCase.facts.processing_purpose}
              </span>
            </div>
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300">
              <span className="text-[11px] text-ink-muted block font-medium">Affected Users:</span>
              <span className="text-xs font-semibold text-ink truncate block mt-0.5">
                {currentCase.facts.affected_users}
              </span>
            </div>
            <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-300">
              <span className="text-[11px] text-ink-muted block font-medium">Data Retention:</span>
              <span className="text-xs font-semibold text-ink truncate block mt-0.5">
                {currentCase.facts.retention_period_days} Days
              </span>
            </div>
          </div>
        </div>

        {/* Right (1 col): Live Spotlights */}
        <div className="space-y-6">
          {/* Active Market Card */}
          {activeMarket && (
            <div className="apple-card space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-800 border border-lavender-200">
                  {activeMarket.market_id}
                </span>
                <span className="text-xs font-semibold text-lavender-700 bg-lavender-50 px-2 py-0.5 rounded-full border border-lavender-200">
                  {activeMarket.state}
                </span>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-ink-muted block mb-1 uppercase tracking-wider">
                  Target Question:
                </span>
                <p className="text-xs text-ink-secondary line-clamp-2 leading-relaxed">
                  {activeMarket.question}
                </p>
              </div>

              <div className="space-y-2 pt-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-ink-secondary font-medium">Consensus Probability:</span>
                  <span className="font-mono font-bold text-lavender-700 text-sm">
                    {(activeMarket.aggregate_probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-cream-200 overflow-hidden border border-cream-300">
                  <div
                    className="h-full bg-lavender-600 rounded-full"
                    style={{ width: `${activeMarket.aggregate_probability * 100}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-ink-muted">
                  <span>Variance: {activeMarket.disagreement_variance}</span>
                  <span>N = {activeMarket.sample_size} Agents</span>
                </div>
              </div>

              <Link
                href="/markets"
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>Commit / Reveal Forecast</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </Link>
            </div>
          )}

          {/* Active Bounty Card */}
          {activeBounty && (
            <div className="apple-card space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-cream-200 text-ink-secondary border border-cream-300">
                  {activeBounty.bounty_id}
                </span>
                <span className="text-xs font-semibold text-lavender-700 bg-lavender-100 px-2.5 py-0.5 rounded-full">
                  +{activeBounty.reward_credits} Credits
                </span>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-ink-muted block mb-1 uppercase tracking-wider">
                  Target Legal Uncertainty:
                </span>
                <p className="text-xs text-ink-secondary line-clamp-2 leading-relaxed">
                  {activeBounty.question}
                </p>
              </div>

              <div className="text-xs text-ink-secondary space-y-1.5 pt-1">
                <div className="flex items-center justify-between">
                  <span>Submissions:</span>
                  <span className="font-semibold text-ink">{activeBounty.submissions.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Status:</span>
                  <span className="text-amber-800 font-semibold">{activeBounty.state}</span>
                </div>
              </div>

              <Link
                href="/bounties"
                className="apple-btn-secondary w-full text-xs py-2 justify-center"
              >
                <span>View Evidence & Rubric</span>
                <ArrowRight className="w-3.5 h-3.5 text-lavender-600" />
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* ── Settlement Audit Trail: Apple Table Utility ── */}
      <section className="apple-card space-y-5">
        <div className="flex items-center justify-between border-b border-cream-200 pb-4">
          <div>
            <h3 className="text-base font-semibold text-ink font-appleDisplay">
              Recent Protocol Events & Settlement Audit
            </h3>
            <p className="text-xs text-ink-muted">
              Verified cryptographic transaction receipts and hash proofs on Sepolia testnet.
            </p>
          </div>
          <Link
            href="/audit"
            className="text-xs text-lavender-700 hover:text-lavender-900 flex items-center gap-1 font-semibold"
          >
            <span>Full Audit Explorer</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-cream-200">
          {auditRecords.slice(0, 4).map((record) => (
            <div key={record.id} className="py-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-semibold bg-cream-200 text-ink">
                  {record.event_type}
                </span>
                <span className="text-ink font-mono text-[11px]">{record.target_id}</span>
              </div>
              <div className="flex items-center gap-4 text-ink-muted">
                <a
                  href={`https://sepolia.etherscan.io/tx/${record.tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[11px] text-lavender-700 hover:underline flex items-center gap-1"
                >
                  <span>Tx: {record.tx_hash.slice(0, 10)}...{record.tx_hash.slice(-8)}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
                <span className="text-[11px]">{new Date(record.timestamp).toLocaleTimeString()}</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-lavender-100 text-lavender-700 border border-lavender-200">
                  {record.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

