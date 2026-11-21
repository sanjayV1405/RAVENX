"use client";

import React, { useState } from "react";
import { Menu } from "lucide-react";
import { Sidebar } from "./Sidebar";
import { TopHeader } from "./TopHeader";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div
      className="min-h-screen relative flex flex-col antialiased selection:bg-[#DC2626] selection:text-white"
      style={{
        background: "linear-gradient(180deg, #F5F6FA 0%, #EDEFF5 100%)",
      }}
    >
      {/* Background ambient pearlescent glow pools */}
      <div
        className="fixed top-0 left-1/4 w-[600px] h-[350px] rounded-full pointer-events-none opacity-40 blur-[120px]"
        style={{
          background: "radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(220, 38, 38, 0.04) 100%)",
        }}
      />
      <div
        className="fixed bottom-0 right-10 w-[500px] h-[350px] rounded-full pointer-events-none opacity-30 blur-[130px]"
        style={{
          background: "radial-gradient(circle, rgba(220, 38, 38, 0.06) 0%, transparent 70%)",
        }}
      />

      {/* Floating Graphite Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Workspace Area (offset by sidebar on desktop) */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-[274px] p-4 lg:p-6 lg:pt-3">
        {/* Mobile Header Bar */}
        <div className="lg:hidden flex items-center justify-between p-3 rounded-2xl bg-white/75 border border-white/80 shadow-sm backdrop-blur-md mb-4">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-xl text-[#20232B] hover:bg-gray-100 transition-colors"
            aria-label="Open Navigation"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-black text-sm tracking-tight text-[#20232B]">
            RAVEN<span className="text-[#DC2626]">X</span> AI
          </span>
          <div className="w-7 h-7 rounded-full bg-[#181A22] text-white text-[10px] font-bold flex items-center justify-center">
            SV
          </div>
        </div>

        {/* Global Desktop TopHeader */}
        <TopHeader />

        {/* Page Main Content */}
        <main className="flex-1 min-w-0 pb-12">{children}</main>
      </div>
    </div>
  );
}

export default AppShell;
