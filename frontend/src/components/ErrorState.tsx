"use client";

import React from "react";
import { AlertOctagon, RefreshCw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message = "An unexpected error occurred. Please try again.",
  onRetry
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in-up">
      <div className="w-16 h-16 rounded-2xl bg-rose-950/30 border border-rose-800/40 flex items-center justify-center mb-4">
        <AlertOctagon className="w-7 h-7 text-rose-400" />
      </div>
      <h3 className="text-sm font-bold text-rose-300 mb-1">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm leading-relaxed mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 text-xs font-semibold transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};
