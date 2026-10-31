"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { Radio, Database } from "lucide-react";

export const LiveOrSampleBadge: React.FC = () => {
  const { isLiveChain, toggleLiveChain } = useStore();

  return (
    <button
      onClick={toggleLiveChain}
      className={`group relative flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold transition-all duration-150 active:scale-[0.97] border ${
        isLiveChain
          ? "bg-bubblegum-soft text-bubblegum-deep border-hairline shadow-soft"
          : "bg-cloud text-muted border-hairline hover:border-bubblegum"
      }`}
      title={
        isLiveChain
          ? "Sepolia testnet, single-deployer demo (Click to toggle)"
          : "No live data (Click to toggle)"
      }
    >
      {isLiveChain ? (
        <>
          <Radio className="w-3.5 h-3.5 text-bubblegum-deep" />
          <span className="font-semibold text-bubblegum-deep">Sepolia testnet, single-deployer demo</span>
          <span className="w-2 h-2 rounded-full bg-bubblegum pulse-dot" />
        </>
      ) : (
        <>
          <Database className="w-3.5 h-3.5 text-muted" />
          <span className="font-medium text-muted">No live data</span>
          <span className="w-1.5 h-1.5 rounded-full bg-muted/40" />
        </>
      )}

      {/* Tooltip */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 hidden group-hover:block z-50 pointer-events-none animate-fade-in-up">
        <div className="px-3 py-1.5 rounded-full bg-white backdrop-blur-md border border-hairline text-[11px] text-ink whitespace-nowrap shadow-soft">
          {isLiveChain
            ? "Connected to Sepolia Testnet receipts."
            : "No active live network connection."}
        </div>
      </div>
    </button>
  );
};
