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

import { api } from "@/lib/api";

export default function AuditExplorerPage() {
  const { auditRecords, contractAddresses, isLiveChain } = useStore();
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [sourceFilter, setSourceFilter] = useState<string>("ALL");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // Option C Independent Verifier State
  const [isVerifierOpen, setIsVerifierOpen] = useState(false);
  const [packageJsonInput, setPackageJsonInput] = useState("");
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifierError, setVerifierError] = useState<string | null>(null);

  const handleVerifyPackage = async () => {
    if (!packageJsonInput.trim()) {
      setVerifierError("Please paste an audit package JSON.");
      return;
    }
    setVerifierError(null);
    setIsVerifying(true);
    try {
      const parsed = JSON.parse(packageJsonInput);
      const res = await api.verifyAuditPackage(parsed);
      setVerificationResult(res);
    } catch (e: any) {
      setVerifierError(`Verification error: ${e.message}`);
    } finally {
      setIsVerifying(false);
    }
  };

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
      const matchesSource =
        sourceFilter === "ALL" ||
        (a.source_type || "SAMPLE_FIXTURE") === sourceFilter;

      return matchesSearch && matchesType && matchesStatus && matchesSource;
    });
  }, [auditRecords, search, eventTypeFilter, statusFilter, sourceFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredAudit.length / itemsPerPage));
  const paginatedAudit = filteredAudit.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const getStatusBadge = (status: "CONFIRMED" | "PENDING" | "REVERTED") => {
    switch (status) {
      case "CONFIRMED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Check className="w-3 h-3 text-emerald-600" />
            CONFIRMED
          </span>
        );
      case "PENDING":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" />
            PENDING
          </span>
        );
      case "REVERTED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertTriangle className="w-3 h-3 text-rose-600" />
            REVERTED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-cream-200 text-ink-secondary">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Header */}
      <div className="apple-card p-6 sm:p-8 rounded-[18px] bg-white border border-cream-300 shadow-apple-card space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-700 border border-lavender-200">
                §16.7
              </span>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink">
                Protocol Audit Explorer
              </h1>
            </div>
            <p className="text-[15px] text-ink-secondary leading-relaxed">
              Public tamper-evident ledger of smart contract addresses, lifecycle transitions, cryptographic commitments, evidence digests, and settlement proofs. Records with the &apos;Sepolia Receipt&apos; badge link directly to confirmed transactions on Sepolia Etherscan.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-ink bg-cream-100 px-3.5 py-1.5 rounded-full border border-cream-200 font-mono shadow-apple-sm">
            <Network className="w-4 h-4 text-lavender-600" />
            <span>ChainId: {contractAddresses.chainId} ({contractAddresses.networkName})</span>
          </div>
        </div>

        {/* Contract Address Registry (§12.2, §16.7) */}
        <div className="space-y-2.5">
          <span className="text-xs font-bold text-ink uppercase tracking-wider block">
            Deployed Smart Contract Modules:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {[
              { name: "CaseRegistry", address: contractAddresses.CaseRegistry, desc: "FR-001..FR-004 scope versioning" },
              { name: "AgentRegistry", address: contractAddresses.AgentRegistry, desc: "PRD §8 agent role authorizations" },
              { name: "PredictionMarket", address: contractAddresses.PredictionMarket, desc: "§10 commit-reveal markets" },
              { name: "EvidenceBounty", address: contractAddresses.EvidenceBounty, desc: "§11 evidence bounty rubric" },
              { name: "ReputationSettlement", address: contractAddresses.ReputationSettlement, desc: "FR-048 proper scoring settlement" }
            ].map((c) => (
              <div
                key={c.name}
                className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 space-y-1.5 hover:border-lavender-300 hover:shadow-apple-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-lavender-700">{c.name}</span>
                  <button
                    onClick={() => copyToClipboard(c.name, c.address)}
                    className="p-1 rounded-full text-ink-tertiary hover:text-ink hover:bg-cream-200 transition-colors"
                    title="Copy Address"
                  >
                    {copiedKey === c.name ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="font-mono text-[11px] text-ink font-medium truncate">{c.address}</div>
                <div className="text-[11px] text-ink-secondary">{c.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Option C Independent Audit Verifier Panel */}
      <div className="apple-card p-6 sm:p-8 rounded-[18px] bg-white border border-cream-300 shadow-apple-card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-lavender-100 text-lavender-700 border border-lavender-200">
                Option C Offline Verifier
              </span>
              <h3 className="text-xl font-bold text-ink">Independent Audit Package Verifier</h3>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              Verify any exported VERIDION Audit Package offline. Recomputes canonical decision digests, Merkle root checkpoints, commit-reveal keccak256 hashes, and Brier proper scoring without trusting the server.
            </p>
          </div>

          <button
            onClick={() => setIsVerifierOpen(!isVerifierOpen)}
            className="apple-btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5"
          >
            <ShieldCheck className="w-4 h-4 text-lavender-700" />
            <span>{isVerifierOpen ? "Hide Verifier Console" : "Open Verifier Console"}</span>
          </button>
        </div>

        {isVerifierOpen && (
          <div className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-semibold text-ink block mb-1.5">
                Paste Audit Package JSON or Decision Record:
              </label>
              <textarea
                value={packageJsonInput}
                onChange={(e) => setPackageJsonInput(e.target.value)}
                placeholder='{"manifest": {...}, "decision_record": {...}, "checksums": {...}}'
                rows={6}
                className="w-full font-mono text-xs p-3.5 rounded-[14px] bg-cream-50 border border-cream-300 text-ink focus:outline-none focus:border-lavender-400 focus:ring-1 focus:ring-lavender-300"
              />
            </div>

            <div className="flex items-center justify-between gap-3">
              <span className="text-[11px] text-ink-muted">
                Zero server-trust required: all digests and cryptographic chains verified deterministically.
              </span>
              <button
                onClick={handleVerifyPackage}
                disabled={isVerifying}
                className="apple-btn-primary text-xs py-2 px-4 flex items-center gap-1.5 shadow-sm shrink-0"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>{isVerifying ? "Verifying..." : "Run Cryptographic Verification"}</span>
              </button>
            </div>

            {verifierError && (
              <div className="p-3 rounded-[12px] bg-rose-50 border border-rose-200 text-xs text-rose-800">
                {verifierError}
              </div>
            )}

            {verificationResult && (
              <div className="p-5 rounded-[14px] bg-cream-50 border border-cream-300 space-y-3">
                <div className="flex items-center justify-between border-b border-cream-200 pb-2.5">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-lavender-700" />
                    <span className="text-xs font-bold text-ink">Verification Report Verdict:</span>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold font-mono ${
                    verificationResult.overall_status === "VERIFIED"
                      ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                      : "bg-rose-100 text-rose-800 border border-rose-200"
                  }`}>
                    {verificationResult.overall_status}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 text-xs">
                  {Object.entries(verificationResult.checks || {}).map(([key, check]: [string, any]) => (
                    <div key={key} className="p-2.5 rounded-lg bg-white border border-cream-200 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-ink capitalize text-[11px]">{key.replace(/_/g, " ")}:</span>
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-cream-100 text-ink">
                          {check.status}
                        </span>
                      </div>
                      {check.digest && <div className="text-[10px] font-mono text-ink-muted truncate">Digest: {check.digest}</div>}
                      {check.merkle_checkpoint_root && <div className="text-[10px] font-mono text-ink-muted truncate">Merkle: {check.merkle_checkpoint_root}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Audit Log Table */}
      <div className="apple-card p-6 rounded-[18px] bg-white border border-cream-300 shadow-apple-card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-cream-200 pb-4">
          <div>
            <h3 className="text-base font-bold text-ink">Immutable Event Journal</h3>
            <p className="text-xs text-ink-secondary">
              {isLiveChain ? "Live on-chain transaction log" : "Chronological feed of validated testnet state transitions and benchmark records."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Source Filter */}
            <select
              value={sourceFilter}
              onChange={(e) => {
                setSourceFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-cream-100 border border-cream-200 rounded-full px-3.5 py-1.5 text-xs text-ink font-medium focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Data Sources</option>
              <option value="ON_CHAIN_RECORDED">Recorded Sepolia Receipts</option>
              <option value="SAMPLE_FIXTURE">Sample Benchmark Fixtures</option>
            </select>

            {/* Event Type Filter */}
            <div className="flex items-center gap-1.5 bg-cream-100 border border-cream-200 rounded-full px-3 py-1.5 text-xs text-ink">
              <Filter className="w-3.5 h-3.5 text-ink-tertiary" />
              <select
                value={eventTypeFilter}
                onChange={(e) => {
                  setEventTypeFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="bg-transparent text-xs text-ink focus:outline-none cursor-pointer font-medium"
              >
                {eventTypes.map((t) => (
                  <option key={t} value={t} className="bg-white text-ink">
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
              className="bg-cream-100 border border-cream-200 rounded-full px-3.5 py-1.5 text-xs text-ink font-medium focus:outline-none cursor-pointer"
            >
              <option value="ALL">All Statuses</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="PENDING">Pending</option>
              <option value="REVERTED">Reverted</option>
            </select>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-ink-tertiary absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search target, tx, actor..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setCurrentPage(1);
                }}
                className="pl-8 pr-4 py-1.5 rounded-full bg-cream-100 border border-cream-200 text-xs text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-lavender-600 focus:bg-white w-56 shadow-apple-sm transition-all"
              />
            </div>
          </div>
        </div>

        {filteredAudit.length === 0 ? (
          <EmptyState
            icon={<FileCheck2 className="w-7 h-7 text-ink-tertiary" />}
            title="No Matching Audit Records"
            description="Try clearing your search query or selecting 'All Event Types' to inspect the complete cryptographic journal."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-cream-200 text-ink-secondary font-semibold text-[10px] uppercase tracking-wider bg-cream-50">
                    <th className="py-3 px-3.5">Provenance</th>
                    <th className="py-3 px-3.5">Event Type</th>
                    <th className="py-3 px-3.5">Target ID</th>
                    <th className="py-3 px-3.5">Actor Address</th>
                    <th className="py-3 px-3.5">Block</th>
                    <th className="py-3 px-3.5">Transaction Hash</th>
                    <th className="py-3 px-3.5">Payload Digest</th>
                    <th className="py-3 px-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cream-200">
                  {paginatedAudit.map((row) => (
                    <tr key={row.id} className="hover:bg-cream-50 transition-colors">
                      <td className="py-3 px-3.5">
                        {row.source_type === "ON_CHAIN_RECORDED" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                            <Check className="w-3 h-3 text-emerald-600" />
                            Sepolia Receipt
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cream-200 text-ink-muted border border-cream-300">
                            Sample Demo
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3.5">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-lavender-50 text-lavender-700 border border-lavender-200">
                          {row.event_type}
                        </span>
                      </td>
                      <td className="py-3 px-3.5 font-semibold text-ink">{row.target_id}</td>
                      <td className="py-3 px-3.5 font-mono text-[11px] text-ink-secondary">
                        {row.actor.slice(0, 8)}...{row.actor.slice(-4)}
                      </td>
                      <td className="py-3 px-3.5 font-mono text-[11px] text-ink">{row.block_number}</td>
                      <td className="py-3 px-3.5">
                        {row.source_type === "ON_CHAIN_RECORDED" ? (
                          <a
                            href={`https://sepolia.etherscan.io/tx/${row.tx_hash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-[11px] text-lavender-700 hover:text-lavender-900 flex items-center gap-1 font-medium"
                          >
                            <span>{row.tx_hash.slice(0, 10)}...</span>
                            <ExternalLink className="w-3 h-3 text-lavender-600" />
                          </a>
                        ) : (
                          <span className="font-mono text-[11px] text-ink-muted flex items-center gap-1">
                            <span>{row.tx_hash.slice(0, 10)}...</span>
                            <span className="text-[9px] text-amber-800 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200 font-sans">Simulated</span>
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3.5 font-mono text-[11px] text-ink-tertiary">
                        {row.payload_digest.slice(0, 12)}...
                      </td>
                      <td className="py-3 px-3.5">
                        {getStatusBadge(row.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-3 border-t border-cream-200 text-xs text-ink-secondary">
                <span>
                  Showing {(currentPage - 1) * itemsPerPage + 1}–{Math.min(currentPage * itemsPerPage, filteredAudit.length)} of {filteredAudit.length} records
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="p-1.5 rounded-full bg-cream-100 border border-cream-200 text-ink hover:bg-cream-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="font-mono font-semibold text-ink">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="p-1.5 rounded-full bg-cream-100 border border-cream-200 text-ink hover:bg-cream-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
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
