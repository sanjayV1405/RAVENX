"use client";

import React from "react";
import { cn } from "@/lib/design-tokens";

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export function GlassPanel({
  children,
  className,
  glow = false,
  ...props
}: GlassPanelProps) {
  return (
    <div
      className={cn(
        "aurora-hero-glass relative p-7 lg:p-9 overflow-hidden rounded-3xl",
        className
      )}
      {...props}
    >
      {glow && (
        <div
          className="absolute -right-20 -top-20 w-[420px] h-[420px] rounded-full pointer-events-none opacity-25 blur-3xl"
          style={{
            background: "radial-gradient(circle, rgba(220, 38, 38, 0.3) 0%, transparent 70%)",
          }}
        />
      )}
      {children}
    </div>
  );
}

export default GlassPanel;

