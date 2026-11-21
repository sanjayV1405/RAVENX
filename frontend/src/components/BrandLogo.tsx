import React from "react";
import Link from "next/link";

interface BrandLogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  withTagline?: boolean;
}

export function BrandLogo({ className = "", size = "md", withTagline = false }: BrandLogoProps) {
  const iconSize = size === "sm" ? 22 : size === "lg" ? 36 : 28;
  const textSize = size === "sm" ? "text-base" : size === "lg" ? "text-2xl" : "text-xl";

  return (
    <Link href="/" className={`inline-flex items-center gap-3 group transition-transform ${className}`}>
      <div className="relative flex items-center justify-center">
        {/* Subtle crimson aura */}
        <div className="absolute inset-0 bg-red-600/20 blur-md rounded-lg group-hover:bg-red-600/35 transition-all duration-300" />
        
        {/* Geometric Raven Emblem */}
        <div className="relative bg-[#11141A] border border-[#2B303C] group-hover:border-red-600/50 rounded-lg p-1.5 transition-colors duration-200 shadow-inner">
          <svg
            width={iconSize}
            height={iconSize}
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="transition-transform group-hover:scale-105"
          >
            {/* Wing geometric contours */}
            <path
              d="M4 8L16 2L28 8L22 18L16 26L10 18L4 8Z"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeLinejoin="round"
              className="group-hover:stroke-white transition-colors"
            />
            {/* Inner Crimson Eye / Core Falcon Shard */}
            <path
              d="M16 7L21 12L16 20L11 12L16 7Z"
              fill="#DC2626"
              className="drop-shadow-[0_0_6px_rgba(220,38,38,0.8)]"
            />
            {/* Precision crosshairs */}
            <line x1="16" y1="2" x2="16" y2="30" stroke="#94A3B8" strokeWidth="1" strokeDasharray="2 2" strokeOpacity="0.4" />
          </svg>
        </div>
      </div>

      <div className="flex flex-col">
        <div className="flex items-center gap-1.5 font-bold tracking-tight">
          <span className={`${textSize} tracking-wider text-white font-mono`}>RAVEN</span>
          <span className={`${textSize} text-[#DC2626] font-mono font-extrabold`}>X</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-[#1C202B] text-[#94A3B8] border border-[#282E3E] font-mono uppercase tracking-widest ml-1">
            AI
          </span>
        </div>
        {withTagline && (
          <span className="text-[10px] tracking-wider text-[#94A3B8] uppercase font-medium">
            Intelligence That Sees What Others Miss
          </span>
        )}
      </div>
    </Link>
  );
}

