"use client";

import React from "react";

interface LoadingStateProps {
  /** Number of skeleton rows to render */
  rows?: number;
  /** Variant layout */
  variant?: "card" | "table" | "inline";
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  rows = 3,
  variant = "card"
}) => {
  if (variant === "inline") {
    return (
      <div className="flex items-center gap-2 py-4">
        <span className="spinner w-4 h-4 text-emerald-400" />
        <span className="text-xs text-slate-400">Loading data...</span>
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className="space-y-2 animate-fade-in-up">
        <div className="skeleton h-8 w-full rounded-lg" />
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="skeleton h-12 w-full rounded-lg" style={{ animationDelay: `${i * 100}ms` }} />
        ))}
      </div>
    );
  }

  // card variant
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in-up">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="glass-panel p-5 rounded-2xl space-y-3" style={{ animationDelay: `${i * 80}ms` }}>
          <div className="skeleton h-4 w-3/4 rounded" />
          <div className="skeleton h-3 w-full rounded" />
          <div className="skeleton h-3 w-5/6 rounded" />
          <div className="flex items-center gap-2 pt-2">
            <div className="skeleton h-6 w-16 rounded-full" />
            <div className="skeleton h-6 w-20 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
};
