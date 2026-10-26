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
        console.error("Network switch failed:", err);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-ink/40 backdrop-blur-md transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-white rounded-[22px] p-6 sm:p-7 space-y-5 animate-fade-in-up border border-cream-300 shadow-apple-float">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-full text-ink-tertiary hover:text-ink hover:bg-cream-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Icon */}
        <div className="flex items-center justify-center">
          <div className="w-14 h-14 rounded-[16px] bg-amber-50 border border-amber-200 flex items-center justify-center shadow-apple-sm">
            <AlertTriangle className="w-7 h-7 text-amber-600" />
          </div>
        </div>

        {/* Content */}
        <div className="text-center space-y-1.5">
          <h2 className="text-lg font-bold text-ink">Wrong Network Detected</h2>
          <p className="text-xs text-ink-secondary leading-relaxed">
            VERIDION protocol contracts are deployed on <strong className="text-ink font-semibold">{expectedNetworkName}</strong>.
            {currentChainId && (
              <> You are currently connected to chain ID <strong className="text-amber-700 font-mono font-semibold">{currentChainId}</strong>.</>
            )}
          </p>
        </div>

        {/* Expected Network Info */}
        <div className="p-3.5 rounded-[14px] bg-cream-50 border border-cream-200 text-xs space-y-2">
          <div className="flex items-center justify-between text-ink-secondary">
            <span className="flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-lavender-600" />
              Expected Network:
            </span>
            <span className="font-bold text-ink">{expectedNetworkName}</span>
          </div>
          <div className="flex items-center justify-between text-ink-secondary">
            <span>Chain ID:</span>
            <span className="font-mono text-lavender-700 font-semibold">{expectedChainId}</span>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2 pt-1">
          <button
            onClick={handleSwitchNetwork}
            className="w-full py-3 px-4 rounded-full bg-lavender-600 hover:bg-lavender-700 text-white font-semibold text-xs shadow-apple-sm transition-all"
          >
            Switch to {expectedNetworkName}
          </button>
          <button
            onClick={onClose}
            className="w-full py-2.5 px-4 rounded-full bg-cream-100 hover:bg-cream-200 border border-cream-200 text-ink text-xs font-semibold transition-colors"
          >
            Continue Without Switching
          </button>
        </div>
      </div>
    </div>
  );
};
