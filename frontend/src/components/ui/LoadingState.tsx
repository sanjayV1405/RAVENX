"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/design-tokens";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({
  message = "Analyzing document content...",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "aurora-glass-card p-12 flex flex-col items-center justify-center text-center select-none",
        className
      )}
    >
      <div className="relative flex items-center justify-center w-14 h-14 mb-4">
        <div className="absolute inset-0 rounded-full border-2 border-red-100 border-t-[#DC2626] animate-spin" />
        <Loader2 className="w-6 h-6 text-[#DC2626] animate-pulse" />
      </div>

      <p className="text-sm font-semibold text-[#1A1D26]">{message}</p>
      <p className="text-xs text-[#687080] mt-1">
        Intelligence that sees what others miss
      </p>
    </div>
  );
}

export default LoadingState;

