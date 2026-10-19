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
  FileCheck
} from "lucide-react";

export default function DashboardPage() {
  const { currentCase, markets, bounties, auditRecords, isLiveChain, userCredits } = useStore();

  const activeMarket = markets[0];
  const activeBounty = bounties[0];
  const settlements = auditRecords.filter(
    (a) => a.event_type === "SETTLEMENT_EXECUTED" || a.event_type === "BOUNTY_SETTLED"
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Banner with Clear Mode Delineation (§16.1) */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-950 to-verdion-950 p-6 sm:p-8 shadow-glass">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Decentralized Legal Intelligence Protocol</span>
            </div>
            {/* Mode Banner Indicator (§16.1) */}
            <div
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                isLiveChain
                  ? "bg-emerald-950/70 text-emerald-300 border-emerald-500/40"
                  : "bg-indigo-950/70 text-indigo-300 border-indigo-500/40"
              }`}
            >
              {isLiveChain ? (
                <>
                  <Radio className="w-3 h-3 text-emerald-400" />
                  <span>SEPOLIA TESTNET LIVE MODE</span>
                </>
              ) : (
                <>
                  <Database className="w-3 h-3 text-indigo-400" />
                  <span>CURATED BENCHMARK SAMPLE MODE (§16.1)</span>
                </>
              )}
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Evidence-Grounded Legal Risk Forecasting
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Coordinating specialized autonomous AI swarms, prediction markets, and evidence bounties.
            Contracts enforce commit-reveal integrity, reproducible proper scoring, and verifiable settlement.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Jurisdiction: <strong>European Union (GDPR & AI Act)</strong></span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span>Corpus Digest: <strong className="font-mono text-cyan-300">0x8fa12b...</strong></span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300">
              <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
              <span>Active Agent Roles: <strong>6 Swarm Nodes</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Protocol Metrics Grid (§16.1) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <div className="glass-panel p-5 rounded-2xl space-y-1">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Briefcase className="w-3.5 h-3.5 text-emerald-400" /> Active Cases
          </span>
          <div className="text-2xl font-extrabold text-white">1</div>
          <span className="text-[11px] text-emerald-400">Scope v{currentCase.scope_version} Frozen</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl space-y-1">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-cyan-400" /> Markets
          </span>
          <div className="text-2xl font-extrabold text-white">{markets.length}</div>
          <span className="text-[11px] text-cyan-400">1 Reveal, 1 Settled</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl space-y-1">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Gift className="w-3.5 h-3.5 text-amber-400" /> Bounties
          </span>
          <div className="text-2xl font-extrabold text-white">{bounties.length}</div>
          <span className="text-[11px] text-amber-400">Challenge Window Active</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl space-y-1">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Coins className="w-3.5 h-3.5 text-purple-400" /> Brier Score
          </span>
          <div className="text-2xl font-extrabold text-white font-mono">0.0210</div>
          <span className="text-[11px] text-emerald-400">97.9% Proper Calibration</span>
        </div>

        <div className="glass-panel p-5 rounded-2xl space-y-1 col-span-2 sm:col-span-1">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <FileCheck className="w-3.5 h-3.5 text-teal-400" /> Settlements
          </span>
          <div className="text-2xl font-extrabold text-white font-mono">{settlements.length}</div>
          <span className="text-[11px] text-teal-400">On-Chain Verified</span>
        </div>
      </div>

      {/* Main Sections: Case Spotlight & Market/Bounty Quick Views */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left (2 cols): Active Case Spotlight (§16.2) */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-3xl space-y-5">
          <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase font-bold">
                  {currentCase.id}
                </span>
                <span className="text-xs text-slate-400 font-medium">Version {currentCase.scope_version}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {isLiveChain ? "Live Chain Scope" : "Curated Dataset"}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white mt-1.5">{currentCase.title}</h2>
            </div>
            <Link
              href="/cases"
              className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              <span>Open Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-400">Investigative Question:</span>
            <p className="text-xs text-slate-200 bg-slate-950/60 p-3 rounded-xl border border-slate-800 leading-relaxed">
              {currentCase.question}
            </p>
          </div>

          {/* Missing Facts Alert (FR-002) */}
          {currentCase.missing_facts.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/40 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-300">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Missing Material Facts Identified (FR-002):</span>
              </div>
              <ul className="space-y-1 text-xs text-amber-200/90 pl-6 list-disc">
                {currentCase.missing_facts.map((mf, idx) => (
                  <li key={idx}>{mf}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-medium">Purpose:</span>
              <span className="text-xs font-semibold text-slate-200 truncate block">
                {currentCase.facts.processing_purpose}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-medium">Users Affected:</span>
              <span className="text-xs font-semibold text-slate-200 truncate block">
                {currentCase.facts.affected_users}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-medium">Retention Period:</span>
              <span className="text-xs font-semibold text-slate-200 truncate block">
                {currentCase.facts.retention_period_days} Days
              </span>
            </div>
          </div>
        </div>

        {/* Right (1 col): Live Spotlight on Active Market & Bounty */}
        <div className="space-y-6">
          {/* Market Card */}
          {activeMarket && (
            <div className="glass-panel p-5 rounded-3xl space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 uppercase font-bold">
                  {activeMarket.market_id}
                </span>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {activeMarket.state}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-semibold text-slate-400 block mb-1">Target Question:</span>
                <p className="text-xs text-slate-300 line-clamp-2">{activeMarket.question}</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Consensus Forecast:</span>
                  <span className="font-mono font-bold text-cyan-400">
                    {(activeMarket.aggregate_probability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full"
                    style={{ width: `${activeMarket.aggregate_probability * 100}%` }}
                  ></div>
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-500">
                  <span>Disagreement Var: {activeMarket.disagreement_variance}</span>
                  <span>N = {activeMarket.sample_size} Agents</span>
                </div>
              </div>

              <Link
                href="/markets"
                className="w-full py-2 px-3 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>Commit / Reveal Forecast</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* Bounty Card */}
          {activeBounty && (
            <div className="glass-panel p-5 rounded-3xl space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase font-bold">
                  {activeBounty.bounty_id}
                </span>
                <span className="text-xs font-mono font-bold text-emerald-400">
                  +{activeBounty.reward_credits} Credits
                </span>
              </div>

              <div>
                <span className="text-[10px] font-semibold text-slate-400 block mb-1">Target Uncertainty:</span>
                <p className="text-xs text-slate-300 line-clamp-2">{activeBounty.question}</p>
              </div>

              <div className="text-[11px] text-slate-400 space-y-1">
                <div className="flex items-center justify-between">
                  <span>Submissions:</span>
                  <span className="text-slate-200 font-semibold">{activeBounty.submissions.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>State:</span>
                  <span className="text-amber-400 font-semibold">{activeBounty.state}</span>
                </div>
              </div>

              <Link
                href="/bounties"
                className="w-full py-2 px-3 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <span>View Evidence & Rubric</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Recent Settlements & Audit Trail (§16.1, §16.7) */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Recent Protocol Events & Settlement Audit</h3>
            <p className="text-xs text-slate-400">Verified transaction receipts and cryptographic hashes on Sepolia testnet.</p>
          </div>
          <Link
            href="/audit"
            className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold"
          >
            <span>Full Audit Explorer</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="divide-y divide-slate-800/80">
          {auditRecords.slice(0, 4).map((record) => (
            <div key={record.id} className="py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300">
                  {record.event_type}
                </span>
                <span className="text-slate-300 font-mono text-[11px]">{record.target_id}</span>
              </div>
              <div className="flex items-center gap-4 text-slate-400">
                <a
                  href={`https://sepolia.etherscan.io/tx/${record.tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
                >
                  <span>Tx: {record.tx_hash.slice(0, 10)}...{record.tx_hash.slice(-8)}</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
                <span className="text-[11px]">{new Date(record.timestamp).toLocaleTimeString()}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40">
                  {record.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
