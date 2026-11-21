import React from "react";
import Link from "next/link";
import { BrandLogo } from "@/components/BrandLogo";
import { Shield, Lock, Terminal, FileCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full bg-[#08090C] border-t border-[#1C202B] py-12 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-[#181D26]">
          {/* Brand info */}
          <div className="md:col-span-2 space-y-4">
            <BrandLogo size="md" withTagline={true} />
            <p className="text-sm text-[#94A3B8] max-w-md leading-relaxed">
              Advanced document intelligence platform engineered to detect nuanced typographical, structural, layout, and cross-consistency defects that general LLMs miss.
            </p>
            <div className="flex items-center gap-4 text-xs text-[#64748B]">
              <span className="flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-emerald-500" />
                Immutable Source Guarantee
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-blue-400" />
                Evidence-Backed Auditing
              </span>
            </div>
          </div>

          {/* Core Pipeline */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#CBD5E1] mb-3">
              Inspection Engine
            </h4>
            <ul className="space-y-2 text-sm text-[#94A3B8]">
              <li className="hover:text-white transition-colors">Visual Layout & Alignment</li>
              <li className="hover:text-white transition-colors">Grammar & Separators</li>
              <li className="hover:text-white transition-colors">Entity Consistency</li>
              <li className="hover:text-white transition-colors">Table & Hierarchy Audit</li>
              <li className="hover:text-white transition-colors">Requirements Validation</li>
            </ul>
          </div>

          {/* Platform & Docs */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#CBD5E1] mb-3">
              Developer & Specs
            </h4>
            <ul className="space-y-2 text-sm text-[#94A3B8]">
              <li>
                <a href="http://localhost:8000/api/v1/docs" target="_blank" rel="noreferrer" className="hover:text-white transition-colors flex items-center gap-1">
                  <span>FastAPI Swagger</span>
                </a>
              </li>
              <li>
                <Link href="/dashboard" className="hover:text-white transition-colors">
                  System Dashboard
                </Link>
              </li>
              <li>
                <Link href="/settings" className="hover:text-white transition-colors">
                  Provider Adapter Setup
                </Link>
              </li>
              <li className="text-xs text-[#64748B] pt-2">
                Phase 1: Foundation Architecture
              </li>
            </ul>
          </div>
        </div>

        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-[#64748B] gap-4">
          <div>
            © {new Date().getFullYear()} RAVENX AI. Built with precision for enterprise document intelligence.
          </div>
          <div className="flex items-center gap-6">
            <span>Graphite Black / Crimson Edition</span>
            <span>v0.1.0 Foundation</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

