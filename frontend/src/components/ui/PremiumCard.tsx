"use client";

import React from "react";
import { cn } from "@/lib/design-tokens";

type CardVariant = "solid" | "glass" | "graphite";

interface PremiumCardProps {
  variant?: CardVariant;
  className?: string;
  children: React.ReactNode;
  noPadding?: boolean;
  hover?: boolean;
  onClick?: () => void;
}

const variantStyles: Record<CardVariant, React.CSSProperties> = {
  solid: {
    background: "#FFFFFF",
    border: "1px solid #DDE0E6",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)",
  },
  glass: {
    background: "rgba(255,255,255,0.68)",
    backdropFilter: "blur(12px)",
    WebkitBackdropFilter: "blur(12px)",
    border: "1px solid rgba(255,255,255,0.4)",
  },
  graphite: {
    background: "#20232B",
    border: "1px solid #2A2D37",
  },
};

export function PremiumCard({
  variant = "solid",
  className,
  children,
  noPadding = false,
  hover = false,
  onClick,
}: PremiumCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl transition-all duration-200",
        !noPadding && "p-5",
        hover &&
          "hover:shadow-md hover:-translate-y-0.5 cursor-pointer",
        onClick && "cursor-pointer",
        className
      )}
      style={variantStyles[variant]}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

export default PremiumCard;

