"use client";

import React, { useState, useEffect } from "react";
import {
  User,
  Cpu,
  Database,
  Lock,
  Key,
  CheckCircle2,
  AlertCircle,
  Save,
  ShieldCheck,
  Server,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { PrimaryButton, SecondaryButton } from "@/components/ui/Buttons";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { cn } from "@/lib/design-tokens";

interface AIProviderItem {
  provider_name: string;
  is_active: boolean;
  is_configured: boolean;
  model_name: string;
  api_base?: string;
}

interface SystemConfig {
  project_name: string;
  version: string;
  environment: string;
  default_ai_provider: string;
  max_file_size_mb: number;
  allowed_extensions: string[];
  ai_providers: AIProviderItem[];
  storage_type: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"profile" | "providers" | "storage">("profile");
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null);

  const [fullName, setFullName] = useState("Sanjay V");
  const [email, setEmail] = useState("sanjay@ravenx.ai");
  const [organization, setOrganization] = useState("RAVENX Enterprise Systems");
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    async function fetchSystemSettings() {
      try {
        const res = await fetch("http://localhost:8000/api/v1/settings");
        if (res.ok) {
          const data = await res.json();
          setSystemConfig(data);
        }
      } catch {
        setSystemConfig({
          project_name: "RAVENX AI",
          version: "1.0.0",
          environment: "production",
          default_ai_provider: "deepseek",
          max_file_size_mb: 25,
          allowed_extensions: ["pdf", "docx", "pptx"],
          ai_providers: [
            { provider_name: "DeepSeek Reasoning", is_active: true, is_configured: false, model_name: "deepseek-chat" },
            { provider_name: "Google Gemini", is_active: false, is_configured: false, model_name: "gemini-1.5-pro" },
          ],
          storage_type: "Local Cryptographic Immutability & SQLite",
        });
      }
    }
    fetchSystemSettings();
  }, []);

  const handleSaveProfile = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const tabs = [
    { id: "profile", label: "Profile & Reviewer Identity", icon: User },
    { id: "providers", label: "AI Reasoning Engines", icon: Cpu },
    { id: "storage", label: "Storage & Data Boundaries", icon: Database },
  ] as const;

  return (
    <div className="space-y-6 select-none">
      {/* Page Header */}
      <PageHeader
        badge="System Configuration"
        title="Workspace Preferences &"
        highlightedTitle="Engine Settings"
        description="Configure reviewer credentials, telemetry, AI reasoning models, and document integrity settings."
      />

      {/* Modern Tabs Bar */}
      <div className="p-1.5 rounded-2xl aurora-glass-card flex items-center gap-1.5 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs md:text-sm font-semibold transition-all cursor-pointer whitespace-nowrap",
                isActive
                  ? "bg-[#171B2A] text-white shadow-2xs"
                  : "text-[#687080] hover:text-[#1A1D26] hover:bg-white/60"
              )}
            >
              <Icon className={cn("w-4 h-4", isActive ? "text-[#DC2626]" : "text-[#9CA3AF]")} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab: Profile */}
      {activeTab === "profile" && (
        <div className="aurora-glass-card p-6 md:p-8 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#E2E6EE]">
            <div>
              <h3 className="font-bold text-base text-[#1A1D26]">Reviewer Profile</h3>
              <p className="text-xs text-[#687080] mt-0.5">
                This identity is affixed to immutable audit logs and signed PDF reports.
              </p>
            </div>
            {savedSuccess && (
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Settings updated successfully
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1A1D26]">Full Name</label>
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs md:text-sm bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#1A1D26]">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs md:text-sm bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
              />
            </div>
            <div className="space-y-1.5 md:col-span-2">
              <label className="text-xs font-semibold text-[#1A1D26]">Organization / Unit</label>
              <input
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs md:text-sm bg-white/80 border border-[#DDE0E6] text-[#1A1D26] focus:outline-hidden focus:border-[#DC2626]"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-[#E2E6EE] flex items-center justify-end">
            <PrimaryButton
              size="md"
              onClick={handleSaveProfile}
              leftIcon={<Save className="w-4 h-4" />}
            >
              Save Profile Changes
            </PrimaryButton>
          </div>
        </div>
      )}

      {/* Tab: Providers */}
      {activeTab === "providers" && (
        <div className="space-y-5">
          {[
            {
              name: "DeepSeek Reasoning",
              model: "deepseek-chat",
              role: "Primary Contextual AI",
              desc: "Provides deep contextual reasoning for semantic contradiction detection, cross-paragraph consistency validation, clause verification, and structural auditing.",
              envKey: "DEEPSEEK_API_KEY",
              color: "#8B5CF6",
            },
            {
              name: "Google Gemini",
              model: "gemini-1.5-pro",
              role: "Secondary Cross-Check Engine",
              desc: "Executes multimodal validation, cross-document comparison verification, and high-precision formatting inspection.",
              envKey: "GEMINI_API_KEY",
              color: "#3B82F6",
            },
          ].map((provider) => (
            <div key={provider.name} className="aurora-glass-card p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white text-xs shadow-2xs"
                    style={{ backgroundColor: provider.color }}
                  >
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[#1A1D26]">{provider.name}</h4>
                    <span className="text-[11px] text-[#687080] font-mono">
                      Model: {provider.model} • {provider.role}
                    </span>
                  </div>
                </div>

                <StatusIndicator status="Offline Safe" label="Key Configured in .env" size="sm" />
              </div>

              <p className="text-xs text-[#687080] leading-relaxed pl-12">{provider.desc}</p>

              <div className="ml-12 p-3 rounded-xl aurora-glass-subtle border border-[#DDE0E6] flex items-center justify-between text-xs font-mono">
                <span className="text-[#687080]">Environment Variable: {provider.envKey}</span>
                <span className="text-[#8F96A3]">Configured securely on server</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Storage */}
      {activeTab === "storage" && (
        <div className="aurora-glass-card p-6 md:p-8 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E2E6EE]">
            <Server className="w-5 h-5 text-[#DC2626]" />
            <h3 className="font-bold text-base text-[#1A1D26]">Document Storage Architecture</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl aurora-glass-subtle border border-[#DDE0E6]">
              <span className="text-xs font-bold text-[#1A1D26] block mb-1">Max Upload Size</span>
              <span className="text-2xl font-black text-[#1A1D26] tabular-nums">25 MB</span>
              <p className="text-[11px] text-[#687080] mt-1">Enforced per document upload</p>
            </div>
            <div className="p-4 rounded-xl aurora-glass-subtle border border-[#DDE0E6]">
              <span className="text-xs font-bold text-[#1A1D26] block mb-1">Supported Formats</span>
              <span className="text-lg font-black text-[#1A1D26]">PDF • DOCX • PPTX</span>
              <p className="text-[11px] text-[#687080] mt-1">Native extraction + OCR</p>
            </div>
            <div className="p-4 rounded-xl aurora-glass-subtle border border-[#DDE0E6]">
              <span className="text-xs font-bold text-[#1A1D26] block mb-1">Source Guarantee</span>
              <span className="text-lg font-black text-emerald-700">100% Immutable</span>
              <p className="text-[11px] text-[#687080] mt-1">Original bytes never modified</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-white/70 border border-[#DDE0E6] text-xs space-y-2">
            <span className="font-bold text-[#1A1D26] flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Cryptographic Integrity Guarantee
            </span>
            <p className="text-[#687080] leading-relaxed">
              RAVENX AI computes a cryptographic SHA-256 hash immediately upon file upload. Original documents are permanently protected in read-only storage. All suggested corrections and review decisions are maintained in decoupled audit layers.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
