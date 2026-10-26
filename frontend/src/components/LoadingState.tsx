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
        <span className="w-4 h-4 rounded-full border-2 border-lavender-600 border-t-transparent animate-spin" />
        <span className="text-xs text-ink-secondary font-medium">Loading data...</span>
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className="space-y-2.5 animate-fade-in-up">
        <div className="h-9 w-full rounded-[12px] bg-cream-200 animate-pulse" />
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="h-12 w-full rounded-[12px] bg-cream-100 animate-pulse"
            style={{ animationDelay: `${i * 100}ms` }}
          />
        ))}
      </div>
    );
  }

  // card variant
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in-up">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="p-5 rounded-[18px] bg-white border border-cream-300 shadow-apple-card space-y-3"
          style={{ animationDelay: `${i * 80}ms` }}
        >
          <div className="h-4 w-3/4 rounded-full bg-cream-200 animate-pulse" />
          <div className="h-3 w-full rounded-full bg-cream-100 animate-pulse" />
          <div className="h-3 w-5/6 rounded-full bg-cream-100 animate-pulse" />
          <div className="flex items-center gap-2 pt-2">
            <div className="h-6 w-16 rounded-full bg-cream-200 animate-pulse" />
            <div className="h-6 w-20 rounded-full bg-cream-200 animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
};
