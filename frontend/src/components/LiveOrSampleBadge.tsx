"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { Database, Radio } from "lucide-react";

export const LiveOrSampleBadge: React.FC = () => {
  const { isLiveChain, toggleLiveChain } = useStore();

  return (
    <button
      onClick={toggleLiveChain}
      className={`group relative flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-medium transition-all duration-150 active:scale-[0.97] border ${
        isLiveChain
          ? "bg-lavender-100 text-lavender-700 border-lavender-300 shadow-sm"
          : "bg-cream-200 text-ink-secondary border-cream-300 hover:border-cream-400"
      }`}
      title={
        isLiveChain
          ? "LIVE TESTNET: Interacting with Sepolia contracts. Click to switch to sample data."
          : "SAMPLE DATA: Viewing curated reproducible dataset. Click to switch to live testnet."
      }
    >
      {isLiveChain ? (
        <>
          <Radio className="w-3.5 h-3.5 text-lavender-600" />
          <span className="font-semibold text-lavender-800">Live Testnet</span>
          <span className="w-2 h-2 rounded-full bg-lavender-600 pulse-dot" />
        </>
      ) : (
        <>
          <Database className="w-3.5 h-3.5 text-ink-secondary" />
          <span className="font-medium">Sample Data</span>
          <span className="w-1.5 h-1.5 rounded-full bg-cream-500" />
        </>
      )}

      {/* Apple Frosted Tooltip */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 hidden group-hover:block z-50 pointer-events-none animate-fade-in-up">
        <div className="px-3 py-1.5 rounded-full bg-white/95 backdrop-blur-md border border-cream-300 text-[11px] text-ink whitespace-nowrap shadow-apple">
          {isLiveChain
            ? "Connected to Sepolia Testnet. Click to switch to benchmark sample."
            : "Curated benchmark dataset (§16.1). Click to switch to live testnet."}
        </div>
      </div>
    </button>
  );
};

