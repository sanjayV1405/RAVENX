"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Home,
  Search,
  CheckSquare,
  GitCompare,
  History,
  Settings,
  Plus,
  ArrowRight,
  Activity,
  X,
} from "lucide-react";
import { RavenXLogo } from "@/components/brand/RavenXLogo";
import { cn } from "@/lib/design-tokens";

const navItems = [
  { label: "Home", href: "/dashboard", icon: Home },
  { label: "Correct Document", href: "/inspection", icon: Search },
  { label: "My Documents", href: "/audit-history", icon: History },
  { label: "Settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard" || pathname === "/";
    return pathname.startsWith(href);
  };

  const sidebarBody = (
    <div className="flex flex-col h-full justify-between p-4 relative overflow-hidden select-none">
      {/* Background ambient red geometric streak in bottom corner (matches reference image) */}
      <div
        className="absolute -bottom-8 -right-8 w-44 h-44 rounded-full pointer-events-none opacity-20 blur-2xl"
        style={{
          background: "radial-gradient(circle, #DC2626 0%, transparent 70%)",
        }}
      />
      <div
        className="absolute bottom-6 right-2 w-28 h-28 pointer-events-none opacity-25"
        style={{
          backgroundImage: `radial-gradient(ellipse at bottom right, rgba(220, 38, 38, 0.4), transparent 70%)`,
        }}
      />

      {/* TOP: Brand Logo Header */}
      <div>
        <div className="flex items-center justify-between pb-6 pt-2 px-2 border-b border-white/[0.06]">
          <RavenXLogo variant="sidebar" size="md" showTagline={true} />
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10"
            aria-label="Close Sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* NAVIGATION ITEMS */}
        <nav className="mt-6 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3.5 px-4 py-2.5 rounded-xl text-xs font-semibold tracking-tight transition-all duration-200 relative group",
                  active
                    ? "aurora-nav-active"
                    : "text-gray-400 hover:text-gray-100 hover:bg-white/[0.05]"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 transition-transform duration-200 group-hover:scale-110",
                    active ? "text-white" : "text-gray-400 group-hover:text-gray-200"
                  )}
                />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* BOTTOM SECTION */}
      <div className="space-y-3 pt-6 z-10">
        {/* Correct Document CTA Button */}
        <Link
          href="/inspection"
          onClick={onClose}
          className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl text-xs font-bold text-white aurora-btn-crimson"
        >
          <Plus className="w-4 h-4" />
          <span>Correct Document</span>
          <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
        </Link>

        {/* Footer Version Info */}
        <div className="px-2 pt-1 flex items-center justify-between text-[10px] font-mono text-gray-500">
          <span>v1.0.0</span>
          <span>RAVENX AI</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Fixed Floating Graphite Sidebar */}
      <aside
        className="hidden lg:flex flex-col fixed left-4 top-4 bottom-4 z-40 rounded-2xl aurora-sidebar-bg"
        style={{ width: 250 }}
      >
        {sidebarBody}
      </aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              key="overlay"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={onClose}
            />
            <motion.aside
              key="drawer"
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", stiffness: 350, damping: 32 }}
              className="fixed left-2 top-2 bottom-2 z-50 w-72 rounded-2xl aurora-sidebar-bg lg:hidden"
            >
              {sidebarBody}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

export default Sidebar;
