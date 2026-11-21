"use client";

import React from "react";
import { FolderSearch } from "lucide-react";
import { cn } from "@/lib/design-tokens";
import { PrimaryButton } from "./Buttons";

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon = FolderSearch,
  title,
  description,
  actionText,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "aurora-glass-card p-10 flex flex-col items-center justify-center text-center select-none",
        className
      )}
    >
      <div className="w-14 h-14 rounded-3xl bg-red-50/80 border border-red-100 flex items-center justify-center text-[#DC2626] mb-4 shadow-sm">
        <Icon className="w-7 h-7" />
      </div>

      <h3 className="text-base font-bold text-[#1A1D26] tracking-tight">{title}</h3>
      <p className="text-xs text-[#687080] max-w-md mt-1.5 leading-relaxed">{description}</p>

      {actionText && onAction && (
        <div className="mt-5">
          <PrimaryButton size="sm" onClick={onAction}>
            {actionText}
          </PrimaryButton>
        </div>
      )}
    </div>
  );
}

export default EmptyState;

