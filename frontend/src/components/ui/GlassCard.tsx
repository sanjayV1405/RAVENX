"use client";

import React from "react";
import { cn } from "@/lib/design-tokens";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "subtle" | "obsidian" | "interactive";
  children: React.ReactNode;
  className?: string;
}

export function GlassCard({
  variant = "default",
  children,
  className,
  ...props
}: GlassCardProps) {
  const variantStyles = {
    default: "aurora-glass-card",
    elevated: "aurora-glass-elevated",
    subtle: "aurora-glass-subtle",
    obsidian: "aurora-obsidian-card text-white",
    interactive: "aurora-glass-card cursor-pointer hover:border-red-200/80 hover:shadow-lg",
  }[variant];

  return (
    <div className={cn(variantStyles, "p-6 relative", className)} {...props}>
      {children}
    </div>
  );
}

export default GlassCard;

