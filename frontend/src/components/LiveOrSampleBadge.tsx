"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { Database, Radio } from "lucide-react";

export const LiveOrSampleBadge: React.FC = () => {
  const { isLiveChain, toggleLiveChain } = useStore();

  return (
    <button
      onClick={toggleLiveChain}
      className="group relative flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all"
      style={{
        background: isLiveChain
          ? "rgba(16, 185, 129, 0.08)"
          : "rgba(99, 102, 241, 0.08)",
        borderColor: isLiveChain
          ? "rgba(16, 185, 129, 0.3)"
          : "rgba(99, 102, 241, 0.3)"
      }}
      title={
        isLiveChain
          ? "LIVE TESTNET: Interacting with Sepolia contracts. Click to switch to sample data."
          : "SAMPLE DATA: Viewing curated reproducible dataset. Click to switch to live testnet."
      }
    >
      {isLiveChain ? (
        <>
          <Radio className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-emerald-300">Live Testnet</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 pulse-dot" />
        </>
      ) : (
        <>
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-indigo-300">Sample Data</span>
          <span className="w-2 h-2 rounded-full bg-indigo-400" />
        </>
      )}

      {/* Tooltip */}
      <div className="absolute -bottom-12 left-1/2 -translate-x-1/2 hidden group-hover:block z-50 pointer-events-none">
        <div className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-[10px] text-slate-300 whitespace-nowrap shadow-xl">
          {isLiveChain
            ? "Connected to Sepolia Testnet. Click to view sample data."
            : "Curated benchmark dataset (§16.1). Click to connect live."}
        </div>
      </div>
    </button>
  );
};
