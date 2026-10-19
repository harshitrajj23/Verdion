"use client";

import React from "react";
import { Network, AlertTriangle, X } from "lucide-react";

interface NetworkPromptModalProps {
  isOpen: boolean;
  onClose: () => void;
  expectedChainId: number;
  expectedNetworkName: string;
  currentChainId?: number;
}

export const NetworkPromptModal: React.FC<NetworkPromptModalProps> = ({
  isOpen,
  onClose,
  expectedChainId,
  expectedNetworkName,
  currentChainId
}) => {
  if (!isOpen) return null;

  const handleSwitchNetwork = async () => {
    if (typeof window !== "undefined" && (window as any).ethereum) {
      try {
        await (window as any).ethereum.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: `0x${expectedChainId.toString(16)}` }]
        });
        onClose();
      } catch (err: any) {
        // If the chain hasn't been added, we could add it here
        console.error("Network switch failed:", err);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md glass-panel rounded-3xl p-6 space-y-5 animate-fade-in-up border-amber-800/40">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Icon */}
        <div className="flex items-center justify-center">
          <div className="w-14 h-14 rounded-2xl bg-amber-950/40 border border-amber-800/40 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-amber-400" />
          </div>
        </div>

        {/* Content */}
        <div className="text-center space-y-2">
          <h2 className="text-lg font-bold text-white">Wrong Network Detected</h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            VERIDION protocol contracts are deployed on <strong className="text-white">{expectedNetworkName}</strong>.
            {currentChainId && (
              <> You are currently connected to chain ID <strong className="text-amber-400 font-mono">{currentChainId}</strong>.</>
            )}
          </p>
        </div>

        {/* Expected Network Info */}
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-cyan-400" />
              Expected Network:
            </span>
            <span className="font-bold text-white">{expectedNetworkName}</span>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Chain ID:</span>
            <span className="font-mono text-cyan-400">{expectedChainId}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2">
          <button
            onClick={handleSwitchNetwork}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-amber-600 to-emerald-600 hover:from-amber-500 hover:to-emerald-500 text-white font-bold text-xs shadow-glow transition-all"
          >
            Switch to {expectedNetworkName}
          </button>
          <button
            onClick={onClose}
            className="w-full py-2 px-4 rounded-xl bg-slate-800/60 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition-colors"
          >
            Continue Without Switching
          </button>
        </div>
      </div>
    </div>
  );
};
