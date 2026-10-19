"use client";

import React from "react";
import { Loader2, CheckCircle2, XCircle, ExternalLink } from "lucide-react";
import type { TxState } from "@/lib/store";

interface TransactionStatusProps {
  txHash: string;
  state: TxState;
  action?: string;
  compact?: boolean;
}

export const TransactionStatus: React.FC<TransactionStatusProps> = ({
  txHash,
  state,
  action,
  compact = false
}) => {
  const chipClass =
    state === "PENDING"
      ? "tx-chip tx-chip-pending"
      : state === "CONFIRMED"
      ? "tx-chip tx-chip-confirmed"
      : "tx-chip tx-chip-reverted";

  const icon =
    state === "PENDING" ? (
      <span className="spinner w-3 h-3 text-amber-400" />
    ) : state === "CONFIRMED" ? (
      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
    ) : (
      <XCircle className="w-3 h-3 text-rose-400" />
    );

  const label =
    state === "PENDING"
      ? "Broadcasting..."
      : state === "CONFIRMED"
      ? "Confirmed"
      : "Reverted";

  if (compact) {
    return (
      <span className={chipClass}>
        {icon}
        <span>{label}</span>
      </span>
    );
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
      <div className="flex items-center gap-2">
        {icon}
        <div>
          {action && (
            <span className="text-slate-400 text-[10px] uppercase font-semibold block">
              {action}
            </span>
          )}
          <span className="font-semibold text-slate-200">{label}</span>
        </div>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <span className="font-mono text-[10px] text-cyan-400">
          {txHash.slice(0, 10)}...{txHash.slice(-6)}
        </span>
        <a
          href={`https://sepolia.etherscan.io/tx/${txHash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-400 hover:text-cyan-300 transition-colors"
          aria-label="View on Etherscan"
        >
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
};
