"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLogo } from "@/components/BrandLogo";
import { 
  FileText, 
  LayoutDashboard, 
  Settings, 
  ShieldCheck, 
  Menu, 
  X, 
  ChevronRight,
  ExternalLink,
  CheckSquare,
  GitCompare,
  History
} from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/inspection", label: "Inspect & Evidence", icon: ShieldCheck },
    { href: "/requirements", label: "Requirements", icon: CheckSquare },
    { href: "/comparison", label: "Compare", icon: GitCompare },
    { href: "/audit-history", label: "Audit History", icon: History },
    { href: "/settings", label: "Settings", icon: Settings },
  ];

  return (
    <nav className="sticky top-0 z-50 w-full bg-[#090A0D]/85 backdrop-blur-md border-b border-[#1E232E]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <BrandLogo size="md" />

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-[#181C25] text-white border border-[#2D3445] shadow-sm"
                      : "text-[#94A3B8] hover:text-[#F1F5F9] hover:bg-[#12151D]"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#DC2626]" : "text-[#64748B]"}`} />
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Right Action */}
          <div className="hidden md:flex items-center gap-3">
            <a
              href="http://localhost:8000/api/v1/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono text-[#94A3B8] hover:text-white bg-[#12151C] border border-[#232938] hover:border-[#384259] transition-colors"
            >
              <span>API v1</span>
              <ExternalLink className="w-3 h-3 text-[#64748B]" />
            </a>

            <Link
              href="/inspection"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-md text-sm font-medium bg-[#DC2626] hover:bg-[#B91C1C] text-white shadow-[0_0_15px_rgba(220,38,38,0.25)] transition-all duration-150 hover:shadow-[0_0_20px_rgba(220,38,38,0.4)]"
            >
              <span>New Inspection</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Mobile hamburger */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-[#94A3B8] hover:text-white hover:bg-[#151922] transition-colors"
              aria-label="Toggle Navigation"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#232938] bg-[#0C0E14] px-4 pt-2 pb-5 space-y-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium ${
                  isActive
                    ? "bg-[#181C25] text-white border border-[#2D3445]"
                    : "text-[#94A3B8] hover:bg-[#12151D] hover:text-white"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#DC2626]" : "text-[#64748B]"}`} />
                {link.label}
              </Link>
            );
          })}
          <div className="pt-3 border-t border-[#1C202B]">
            <Link
              href="/inspection"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-md text-sm font-medium bg-[#DC2626] text-white"
            >
              <span>New Inspection</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}

