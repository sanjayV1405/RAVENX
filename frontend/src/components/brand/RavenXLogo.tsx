"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/design-tokens";

interface RavenXLogoProps {
  variant?: "full" | "compact" | "sidebar" | "showcase" | "mono";
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  showTagline?: boolean;
}

export function RavenXLogo({
  variant = "full",
  size = "md",
  className,
  showTagline = true,
}: RavenXLogoProps) {
  const isSidebar = variant === "sidebar";
  const isShowcase = variant === "showcase";

  // SVG dimensions
  const dims = {
    sm: { icon: 28, text: 15, tag: 8.5 },
    md: { icon: 38, text: 18, tag: 10 },
    lg: { icon: 48, text: 22, tag: 11 },
    xl: { icon: 64, text: 28, tag: 12 },
  }[size];

  // Faceted 3D Origami/Geometric Raven Emblem matching reference images
  const RavenIcon = (
    <motion.svg
      initial={{ opacity: 0, scale: 0.92, rotate: -2 }}
      animate={{ opacity: 1, scale: 1, rotate: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      width={dims.icon}
      height={dims.icon}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="shrink-0 transition-transform duration-300 hover:scale-105"
      aria-label="RAVENX AI Emblem"
    >
      <defs>
        {/* Gradients for faceted low-poly raven */}
        <linearGradient id="beakTop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1E222D" />
          <stop offset="100%" stopColor="#0B0D12" />
        </linearGradient>
        <linearGradient id="beakBottom" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#15171F" />
          <stop offset="100%" stopColor="#07080B" />
        </linearGradient>
        <linearGradient id="headTop" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#2E3444" />
          <stop offset="100%" stopColor="#151821" />
        </linearGradient>
        <linearGradient id="headMid" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#222733" />
          <stop offset="100%" stopColor="#0F1117" />
        </linearGradient>
        <linearGradient id="crestRed" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#EF4444" />
          <stop offset="50%" stopColor="#DC2626" />
          <stop offset="100%" stopColor="#991B1B" />
        </linearGradient>
        <linearGradient id="throatRed" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#DC2626" />
          <stop offset="100%" stopColor="#7F1D1D" />
        </linearGradient>
        <linearGradient id="eyeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FF4D4D" />
          <stop offset="100%" stopColor="#DC2626" />
        </linearGradient>
        <filter id="crimsonFilter" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#DC2626" floodOpacity="0.45" />
        </filter>
      </defs>

      {/* Background Soft Shadow/Aura */}
      <circle cx="50" cy="50" r="42" fill="none" opacity="0.1" />

      {/* Facet: Back Crown / Upper Feathers */}
      <polygon points="46,14 68,26 54,34 36,22" fill="url(#headTop)" />
      
      {/* Facet: Crimson Feather Accent Upper */}
      <polygon points="68,26 88,28 72,40 54,34" fill="url(#crestRed)" filter="url(#crimsonFilter)" />
      <polygon points="72,40 94,44 76,52 60,46" fill="url(#crestRed)" />
      <polygon points="76,52 90,62 68,60 60,46" fill="url(#throatRed)" />

      {/* Facet: Forehead & Brow */}
      <polygon points="36,22 54,34 40,48 24,36" fill="url(#headMid)" />
      <polygon points="40,48 54,34 60,46 44,56" fill="#1A1D27" />

      {/* Facet: Upper Beak (Sharp, Aggressive) */}
      <polygon points="8,44 24,36 40,48" fill="url(#beakTop)" />
      <polygon points="8,44 40,48 34,56" fill="url(#beakBottom)" />

      {/* Facet: Lower Beak / Jaw */}
      <polygon points="18,52 34,56 28,68" fill="#12141C" />

      {/* Facet: Glowing Crimson Eye (Low Poly Diamond) */}
      <polygon points="36,42 42,40 40,46 34,45" fill="url(#eyeGlow)" filter="url(#crimsonFilter)" />
      <circle cx="38" cy="43" r="1.5" fill="#FFFFFF" opacity="0.9" />

      {/* Facet: Cheek & Temple */}
      <polygon points="40,48 44,56 36,66 28,68 34,56" fill="#202532" />
      <polygon points="44,56 60,46 54,68 36,66" fill="#141720" />

      {/* Facet: Neck / Throat with Crimson Splash */}
      <polygon points="36,66 54,68 46,86 28,78" fill="url(#headMid)" />
      <polygon points="54,68 68,60 64,82 46,86" fill="url(#throatRed)" />
      <polygon points="64,82 78,74 72,88 56,92" fill="#7F1D1D" />
      <polygon points="46,86 56,92 38,94" fill="#0C0E14" />
    </motion.svg>
  );

  if (variant === "compact") {
    return <div className={cn("inline-flex items-center", className)}>{RavenIcon}</div>;
  }

  const textColor = isSidebar ? "#FFFFFF" : "#1A1D26";
  const tagColor = isSidebar ? "#8F96A3" : "#687080";

  return (
    <div className={cn("flex items-center gap-3 select-none", className)}>
      {RavenIcon}

      <div className="flex flex-col">
        <div className="flex items-center gap-1 leading-none">
          <span
            className="font-black tracking-tight"
            style={{
              fontSize: dims.text,
              color: textColor,
              letterSpacing: "0.04em",
            }}
          >
            RAVEN<span className="text-[#DC2626]">X</span>
          </span>
          <span
            className="font-black text-[#DC2626]"
            style={{ fontSize: dims.text, letterSpacing: "0.04em" }}
          >
            AI
          </span>
        </div>

        {showTagline && (
          <span
            className="font-medium tracking-tight mt-1 line-clamp-1"
            style={{
              fontSize: dims.tag,
              color: tagColor,
              letterSpacing: "-0.01em",
            }}
          >
            Intelligence That Sees What Others Miss.
          </span>
        )}
      </div>
    </div>
  );
}

export default RavenXLogo;
