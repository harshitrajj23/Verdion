"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Clock, AlertTriangle } from "lucide-react";

interface DeadlineCountdownProps {
  /** ISO timestamp of the deadline */
  deadline: string;
  /** Label describing this deadline */
  label: string;
  /** Accent color theme */
  accent?: "cyan" | "amber" | "rose" | "emerald";
  /** Whether to show compact single-line variant */
  compact?: boolean;
}

const accentMap = {
  cyan: {
    bg: "bg-lavender-50",
    border: "border-lavender-200",
    text: "text-lavender-700",
    icon: "text-lavender-600",
    value: "text-lavender-700"
  },
  amber: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    text: "text-amber-800",
    icon: "text-amber-600",
    value: "text-amber-800"
  },
  rose: {
    bg: "bg-rose-50",
    border: "border-rose-200",
    text: "text-rose-800",
    icon: "text-rose-600",
    value: "text-rose-800"
  },
  emerald: {
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    text: "text-emerald-800",
    icon: "text-emerald-600",
    value: "text-emerald-800"
  }
};

export const DeadlineCountdown: React.FC<DeadlineCountdownProps> = ({
  deadline,
  label,
  accent = "cyan",
  compact = false
}) => {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const { hours, minutes, seconds, isExpired, totalMs } = useMemo(() => {
    const target = new Date(deadline).getTime();
    const diff = target - now;
    if (diff <= 0) {
      return { hours: 0, minutes: 0, seconds: 0, isExpired: true, totalMs: 0 };
    }
    return {
      hours: Math.floor(diff / 3600000),
      minutes: Math.floor((diff % 3600000) / 60000),
      seconds: Math.floor((diff % 60000) / 1000),
      isExpired: false,
      totalMs: diff
    };
  }, [deadline, now]);

  const colors = accentMap[accent];
  const isUrgent = !isExpired && totalMs < 3600000; // under 1 hour

  if (compact) {
    if (isExpired) {
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono text-ink-tertiary">
          <Clock className="w-3 h-3" />
          <span>Expired</span>
        </span>
      );
    }
    return (
      <span className={`flex items-center gap-1 text-[10px] font-mono font-semibold ${isUrgent ? "text-rose-600" : colors.value}`}>
        <Clock className="w-3 h-3" />
        <span>
          {String(hours).padStart(2, "0")}:{String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
        </span>
      </span>
    );
  }

  return (
    <div className={`p-3 rounded-[14px] ${colors.bg} border ${colors.border} space-y-2 shadow-apple-sm`}>
      <div className="flex items-center justify-between">
        <span className={`text-[10px] font-semibold uppercase tracking-wider ${colors.text} flex items-center gap-1.5`}>
          {isUrgent && !isExpired ? (
            <AlertTriangle className={`w-3 h-3 ${colors.icon}`} />
          ) : (
            <Clock className={`w-3 h-3 ${colors.icon}`} />
          )}
          {label}
        </span>
        {isExpired && (
          <span className="text-[10px] font-bold text-ink-tertiary uppercase">Expired</span>
        )}
      </div>

      {!isExpired && (
        <div className="flex items-center gap-3">
          <div className="countdown-segment">
            <span className={`countdown-value font-mono font-bold text-sm ${isUrgent ? "text-rose-600" : colors.value}`}>
              {String(hours).padStart(2, "0")}
            </span>
            <span className="countdown-label text-[10px] text-ink-tertiary">Hrs</span>
          </div>
          <span className="text-ink-tertiary font-mono text-xs">:</span>
          <div className="countdown-segment">
            <span className={`countdown-value font-mono font-bold text-sm ${isUrgent ? "text-rose-600" : colors.value}`}>
              {String(minutes).padStart(2, "0")}
            </span>
            <span className="countdown-label text-[10px] text-ink-tertiary">Min</span>
          </div>
          <span className="text-ink-tertiary font-mono text-xs">:</span>
          <div className="countdown-segment">
            <span className={`countdown-value font-mono font-bold text-sm ${isUrgent ? "text-rose-600" : colors.value}`}>
              {String(seconds).padStart(2, "0")}
            </span>
            <span className="countdown-label text-[10px] text-ink-tertiary">Sec</span>
          </div>
        </div>
      )}
    </div>
  );
};
