"use client";

import React, { useState } from "react";
import { Search, Bell, ChevronDown, User, Sparkles } from "lucide-react";

interface TopHeaderProps {
  onSearch?: (query: string) => void;
}

export function TopHeader({ onSearch }: TopHeaderProps) {
  const [searchVal, setSearchVal] = useState("");

  return (
    <header className="flex items-center justify-between gap-4 py-4 px-2 select-none">
      {/* Search Bar matching reference image */}
      <div className="relative flex-1 max-w-xl">
        <Search className="w-4 h-4 text-[#727989] absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={searchVal}
          onChange={(e) => {
            setSearchVal(e.target.value);
            onSearch?.(e.target.value);
          }}
          placeholder="Search documents, reports... (Ctrl + K)"
          className="w-full pl-11 pr-4 py-2.5 rounded-full text-xs font-medium text-[#20232B] placeholder-[#727989] bg-white/70 border border-white/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] focus:bg-white focus:border-[#CBD2DE] focus:outline-none transition-all duration-200"
          style={{
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
          }}
        />
      </div>

      {/* Right Controls: Notifications & User Profile */}
      <div className="flex items-center gap-3">
        {/* Notification Bell with Badge */}
        <button
          className="relative w-10 h-10 rounded-full flex items-center justify-center bg-white/75 border border-white/90 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:bg-white transition-all duration-200 text-[#20232B]"
          style={{
            backdropFilter: "blur(12px)",
          }}
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4 text-[#20232B]" />
          <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[#DC2626] text-white text-[10px] font-bold flex items-center justify-center shadow-[0_2px_6px_rgba(220,38,38,0.4)]">
            3
          </span>
        </button>

        {/* User Profile Pill */}
        <div
          className="flex items-center gap-2.5 pl-1.5 pr-3 py-1.5 rounded-full bg-white/75 border border-white/90 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:bg-white transition-all duration-200 cursor-pointer"
          style={{
            backdropFilter: "blur(12px)",
          }}
        >
          {/* Avatar circle */}
          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#20232B] to-[#3B4254] text-white font-bold text-xs flex items-center justify-center shadow-inner overflow-hidden border border-white/50">
            <span className="text-[11px]">SV</span>
          </div>
          <span className="text-xs font-bold text-[#20232B] tracking-tight">Sanjay V</span>
          <ChevronDown className="w-3.5 h-3.5 text-[#727989]" />
        </div>
      </div>
    </header>
  );
}

export default TopHeader;

