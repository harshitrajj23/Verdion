"use client";

import React from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center animate-fade-in-up">
      <div className="w-14 h-14 rounded-[16px] bg-cream-100 border border-cream-200 flex items-center justify-center mb-3.5 shadow-apple-sm text-lavender-600">
        {icon || <Inbox className="w-6 h-6 text-ink-tertiary" />}
      </div>
      <h3 className="text-sm font-bold text-ink mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-ink-secondary max-w-sm leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};
