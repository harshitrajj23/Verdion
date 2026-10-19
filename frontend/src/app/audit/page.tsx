"use client";

import React, { useState, useMemo } from "react";
import { useStore } from "@/lib/store";
import { EmptyState } from "@/components/EmptyState";
import {
  FileCheck2,
  ExternalLink,
  ShieldCheck,
  Copy,
  Check,
  Search,
  Filter,
  Network,
  Clock,
  AlertTriangle,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

export default function AuditExplorerPage() {
  const { auditRecords, contractAddresses, isLiveChain } = useStore();
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  const copyToClipboard = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const eventTypes = useMemo(() => {
    const types = Array.from(new Set(auditRecords.map((r) => r.event_type)));
    return ["ALL", ...types];
  }, [auditRecords]);

  const filteredAudit = useMemo(() => {
    return auditRecords.filter((a) => {
      const matchesSearch =
        a.target_id.toLowerCase().includes(search.toLowerCase()) ||
        a.tx_hash.toLowerCase().includes(search.toLowerCase()) ||
        a.event_type.toLowerCase().includes(search.toLowerCase()) ||
        a.actor.toLowerCase().includes(search.toLowerCase());

      const matchesType = eventTypeFilter === "ALL" || a.event_type === eventTypeFilter;
      const matchesStatus = statusFilter === "ALL" || a.status === statusFilter;

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [auditRecords, search, eventTypeFilter, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredAudit.length / itemsPerPage));
  const paginatedAudit = filteredAudit.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const getStatusBadge = (status: "CONFIRMED" | "PENDING" | "REVERTED") => {
    switch (status) {
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/40">
            <Check className="w-3 h-3 text-emerald-400" />
            CONFIRMED
          </span>
        );
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/40">
            <Clock className="w-3 h-3 text-amber-400" />
            PENDING
          </span>
        );
      case "REVERTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-950/80 text-rose-300 border border-rose-500/40">
            <AlertTriangle className="w-3 h-3 text-rose-400" />
            REVERTED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                §16.7
              </span>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white">Protocol Audit Explorer</h1>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Public tamper-evident ledger of smart contract addresses, lifecycle transitions, cryptographic commitments, evidence digests, and settlement proofs.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800 font-mono">
            <Network className="w-4 h-4 text-cyan-400" />
            <span>ChainId: {contractAddresses.chainId} ({contractAddresses.networkName})</span>
          </div>
        </div>

        {/* Contract Address Registry (§12.2, §16.7) */}
        <div className="space-y-2">
          <span className="text-xs font-bold text-white uppercase tracking-wider block">
            Deployed Smart Contract Modules:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {[
              { name: "CaseRegistry", address: contractAddresses.CaseRegistry, desc: "FR-001..FR-004 scope versioning" },
              { name: "AgentRegistry", address: contractAddresses.AgentRegistry, desc: "PRD §8 agent role authorizations" },
              { name: "PredictionMarket", address: contractAddresses.PredictionMarket, desc: "§10 commit-reveal markets" },
              { name: "EvidenceBounty", address: contractAddresses.EvidenceBounty, desc: "§11 evidence bounty rubric" },
              { name: "ReputationSettlement", address: contractAddresses.ReputationSettlement, desc: "FR-048 proper scoring settlement" }
            ].map((c) => (
              <div
                key={c.name}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-emerald-300">{c.name}</span>
                  <button
                    onClick={() => copyToClipboard(c.name, c.address)}
                    className="text-slate-400 hover:text-white"
                    title="Copy Address"
                  >
                    {copiedKey === c.name ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="font-mono text-[10px] text-cyan-400 truncate">{c.address}</div>
                <div className="text-[10px] text-slate-500">{c.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Immutable Event Journal</h3>
            <p className="text-xs text-slate-400">
              {isLiveChain ? "Live on-chain transaction log" : "Chronological feed of validated testnet state transitions."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Event Type Filter */}
            <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1">
              <Filter className="w-3 h-3 text-slate-400" />
              <select
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="bg-transparent text-xs text-slate-300 focus:outline-none cursor-pointer"
              >
                {eventTypes.map((t) => (
                  <option key={t} value={t} className="bg-slate-900 text-slate-200">
                    {t === "ALL" ? "All Event Types" : t}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Statuses</option>
              <option value="CONFIRMED" className="bg-slate-900">Confirmed</option>
              <option value="PENDING" className="bg-slate-900">Pending</option>
              <option value="REVERTED" className="bg-slate-900">Reverted</option>
            </select>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search target, tx, actor..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 w-52"
              />
            </div>
          </div>
        </div>

        {filteredAudit.length === 0 ? (
          <EmptyState
            icon={<FileCheck2 className="w-7 h-7 text-slate-500" />}
            title="No Matching Audit Records"
            description="Try clearing your search query or selecting 'All Event Types' to inspect the complete cryptographic journal."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 font-semibold text-[10px] uppercase">
                    <th className="py-3 px-3">Event Type</th>
                    <th className="py-3 px-3">Target ID</th>
                    <th className="py-3 px-3">Actor Address</th>
                    <th className="py-3 px-3">Block</th>
                    <th className="py-3 px-3">Transaction Hash</th>
                    <th className="py-3 px-3">Payload Digest</th>
                    <th className="py-3 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {paginatedAudit.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300">
                          {row.event_type}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-semibold text-slate-200">{row.target_id}</td>
                      <td className="py-3 px-3 font-mono text-[10px] text-slate-400">
                        {row.actor.slice(0, 8)}...{row.actor.slice(-4)}
                      </td>
                      <td className="py-3 px-3 font-mono text-[11px] text-slate-300">{row.block_number}</td>
                      <td className="py-3 px-3">
                        <a
                          href={`https://sepolia.etherscan.io/tx/${row.tx_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                        >
                          <span>{row.tx_hash.slice(0, 10)}...</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                      <td className="py-3 px-3 font-mono text-[10px] text-slate-500">
                        {row.payload_digest.slice(0, 12)}...
                      </td>
                      <td className="py-3 px-3">
                        {getStatusBadge(row.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-3 border-t border-slate-800 text-xs text-slate-400">
                <span>
                  Showing {(currentPage - 1) * itemsPerPage + 1}–{Math.min(currentPage * itemsPerPage, filteredAudit.length)} of {filteredAudit.length} records
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="font-mono text-white">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
