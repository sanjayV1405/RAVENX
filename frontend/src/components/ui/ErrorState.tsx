"use client";

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "@/lib/design-tokens";
import { SecondaryButton } from "./Buttons";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Connection Notice",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "aurora-glass-card p-8 border border-red-200/80 bg-red-50/40 select-none",
        className
      )}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center shrink-0 text-red-600 mt-0.5">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-red-950 tracking-tight">{title}</h4>
            <p className="text-xs text-red-800/90 mt-1 max-w-xl leading-relaxed">
              {message}
            </p>
          </div>
        </div>

        {onRetry && (
          <div className="shrink-0 self-end md:self-center">
            <SecondaryButton
              size="sm"
              onClick={onRetry}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              className="border-red-200 text-red-800 hover:bg-white"
            >
              Retry Connection
            </SecondaryButton>
          </div>
        )}
      </div>
    </div>
  );
}

export default ErrorState;

