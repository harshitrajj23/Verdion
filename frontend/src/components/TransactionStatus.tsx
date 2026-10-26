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
      ? "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200"
      : state === "CONFIRMED"
      ? "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
      : "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200";

  const icon =
    state === "PENDING" ? (
      <span className="w-3.5 h-3.5 rounded-full border-2 border-amber-600 border-t-transparent animate-spin" />
    ) : state === "CONFIRMED" ? (
      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
    ) : (
      <XCircle className="w-3.5 h-3.5 text-rose-600" />
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
    <div className="flex items-center gap-3 p-3.5 rounded-[14px] bg-white border border-cream-300 text-xs shadow-apple-card">
      <div className="flex items-center gap-2.5">
        {icon}
        <div>
          {action && (
            <span className="text-ink-secondary text-[10px] uppercase font-semibold block">
              {action}
            </span>
          )}
          <span className="font-semibold text-ink">{label}</span>
        </div>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <span className="font-mono text-[11px] text-lavender-700 font-medium">
          {txHash.slice(0, 10)}...{txHash.slice(-6)}
        </span>
        <a
          href={`https://sepolia.etherscan.io/tx/${txHash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-ink-tertiary hover:text-lavender-700 transition-colors"
          aria-label="View on Etherscan"
        >
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>
    </div>
  );
};
