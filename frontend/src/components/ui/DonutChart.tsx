"use client";

import React from "react";

interface DonutChartProps {
  totalIssues?: number;
  critical?: number;
  high?: number;
  medium?: number;
  low?: number;
}

export function DonutChart({
  totalIssues = 0,
  critical = 0,
  high = 0,
  medium = 0,
  low = 0,
}: DonutChartProps) {
  const sum = critical + high + medium + low;
  const isZero = sum === 0;

  const pCritical = isZero ? 0 : Math.round((critical / sum) * 100);
  const pHigh = isZero ? 0 : Math.round((high / sum) * 100);
  const pMedium = isZero ? 0 : Math.round((medium / sum) * 100);
  const pLow = isZero ? 0 : Math.max(0, 100 - (pCritical + pHigh + pMedium));

  // SVG circular arc calculations
  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ~314.16

  const strokeCrit = (pCritical / 100) * circumference;
  const strokeHigh = (pHigh / 100) * circumference;
  const strokeMed = (pMedium / 100) * circumference;
  const strokeLow = (pLow / 100) * circumference;

  const offsetCrit = 0;
  const offsetHigh = -strokeCrit;
  const offsetMed = -(strokeCrit + strokeHigh);
  const offsetLow = -(strokeCrit + strokeHigh + strokeMed);

  return (
    <div className="flex items-center justify-between gap-6 py-2 select-none">
      {/* Donut SVG with central count */}
      <div className="relative w-36 h-36 flex items-center justify-center shrink-0">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 130 130">
          {/* Base Track */}
          <circle
            cx="65"
            cy="65"
            r={radius}
            fill="transparent"
            stroke={isZero ? "#10B981" : "#E5E7EB"}
            strokeWidth="14"
            opacity={isZero ? 0.35 : 1}
          />

          {!isZero && (
            <>
              {/* Critical (Crimson Red) */}
              {pCritical > 0 && (
                <circle
                  cx="65"
                  cy="65"
                  r={radius}
                  fill="transparent"
                  stroke="#DC2626"
                  strokeWidth="14"
                  strokeDasharray={`${strokeCrit} ${circumference}`}
                  strokeDashoffset={offsetCrit}
                />
              )}

              {/* High (Amber / Orange) */}
              {pHigh > 0 && (
                <circle
                  cx="65"
                  cy="65"
                  r={radius}
                  fill="transparent"
                  stroke="#F59E0B"
                  strokeWidth="14"
                  strokeDasharray={`${strokeHigh} ${circumference}`}
                  strokeDashoffset={offsetHigh}
                />
              )}

              {/* Medium (Blue) */}
              {pMedium > 0 && (
                <circle
                  cx="65"
                  cy="65"
                  r={radius}
                  fill="transparent"
                  stroke="#3B82F6"
                  strokeWidth="14"
                  strokeDasharray={`${strokeMed} ${circumference}`}
                  strokeDashoffset={offsetMed}
                />
              )}

              {/* Low (Slate / Gray) */}
              {pLow > 0 && (
                <circle
                  cx="65"
                  cy="65"
                  r={radius}
                  fill="transparent"
                  stroke="#475569"
                  strokeWidth="14"
                  strokeDasharray={`${strokeLow} ${circumference}`}
                  strokeDashoffset={offsetLow}
                />
              )}
            </>
          )}
        </svg>

        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-black text-[#1A1D26] tracking-tight leading-none tabular-nums">
            {totalIssues}
          </span>
          <span className="text-[10px] font-semibold text-[#687080] uppercase tracking-wider mt-1">
            {isZero ? "All Clean" : "Total Issues"}
          </span>
        </div>
      </div>

      {/* Legend list */}
      <div className="flex-1 space-y-2">
        {[
          { label: "Critical", count: critical, pct: pCritical, color: "#DC2626" },
          { label: "High", count: high, pct: pHigh, color: "#F59E0B" },
          { label: "Medium", count: medium, pct: pMedium, color: "#3B82F6" },
          { label: "Low", count: low, pct: pLow, color: "#475569" },
        ].map((item) => (
          <div key={item.label} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: item.color }}
              />
              <span className="font-medium text-[#1A1D26]">{item.label}</span>
            </div>
            <div className="font-mono text-xs tabular-nums">
              <span className="font-bold text-[#1A1D26]">{item.count}</span>{" "}
              <span className="text-[#687080]">({item.pct}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default DonutChart;
