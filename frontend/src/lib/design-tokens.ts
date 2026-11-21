// RAVENX AI — PHASE 5 SIGNATURE DESIGN TOKENS
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const auroraColors = {
  // Base workspaces
  pearlBg: "#F5F6FA",
  pearlSecondary: "#ECEEF4",
  pearlIvory: "#FBFBFC",
  
  // Glass surfaces
  glassPrimary: "rgba(255, 255, 255, 0.72)",
  glassSecondary: "rgba(255, 255, 255, 0.45)",
  glassHighlight: "rgba(255, 255, 255, 0.95)",
  glassBorder: "rgba(255, 255, 255, 0.85)",
  glassBorderSubtle: "rgba(226, 230, 238, 0.65)",

  // Sidebar & Dark Obsidian
  graphiteSidebar: "#171B2A",
  graphiteSidebarDeep: "#11141F",
  graphiteCard: "#151821",
  graphiteBorder: "rgba(255, 255, 255, 0.08)",

  // Typography
  primaryText: "#1A1D26",
  secondaryText: "#687080",
  mutedText: "#9CA3AF",
  lightText: "#FFFFFF",
  lightMuted: "#8F96A3",

  // Signature Crimson Accent
  crimsonPrimary: "#DC2626",
  crimsonDeep: "#B91C1C",
  crimsonGlow: "rgba(220, 38, 38, 0.28)",
  crimsonSubtle: "rgba(220, 38, 38, 0.08)",
  crimsonBorder: "rgba(220, 38, 38, 0.22)",

  // Silver and Borders
  silverBorder: "#DDE0E6",
  silverBorderSubtle: "#E5E8EF",

  // Status Colors
  emeraldAccent: "#10B981",
  emeraldSubtle: "rgba(16, 185, 129, 0.1)",
  amberAccent: "#F59E0B",
  amberSubtle: "rgba(245, 158, 11, 0.1)",
  blueAccent: "#3B82F6",
  blueSubtle: "rgba(59, 130, 246, 0.1)",
  purpleAccent: "#8B5CF6",
  purpleSubtle: "rgba(139, 92, 246, 0.1)",
} as const;

export const auroraTypography = {
  fontSans: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif",
  fontMono: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  
  // Heading & Display scale
  heroHeading: "text-3xl md:text-4xl lg:text-[42px] font-extrabold tracking-tight leading-[1.12]",
  pageHeading: "text-2xl md:text-3xl font-bold tracking-tight text-[#1A1D26]",
  sectionHeading: "text-lg md:text-xl font-bold tracking-tight text-[#1A1D26]",
  cardHeading: "text-sm md:text-base font-semibold text-[#1A1D26]",
  bodyText: "text-sm text-[#687080] leading-relaxed",
  metadata: "text-xs font-medium text-[#8F96A3]",
} as const;

export const severityTokens = {
  CRITICAL: {
    bg: "bg-red-50/80",
    border: "border-red-200",
    text: "text-red-700",
    badge: "bg-red-50 text-red-700 border-red-200",
    indicator: "bg-red-600",
  },
  HIGH: {
    bg: "bg-orange-50/80",
    border: "border-orange-200",
    text: "text-orange-700",
    badge: "bg-orange-50 text-orange-700 border-orange-200",
    indicator: "bg-orange-500",
  },
  MEDIUM: {
    bg: "bg-amber-50/80",
    border: "border-amber-200",
    text: "text-amber-700",
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    indicator: "bg-amber-500",
  },
  LOW: {
    bg: "bg-blue-50/80",
    border: "border-blue-200",
    text: "text-blue-700",
    badge: "bg-blue-50 text-blue-700 border-blue-200",
    indicator: "bg-blue-500",
  },
  INFO: {
    bg: "bg-gray-50/80",
    border: "border-gray-200",
    text: "text-gray-600",
    badge: "bg-gray-50 text-gray-600 border-gray-200",
    indicator: "bg-gray-400",
  },
} as const;

export const statusColors = {
  MET: {
    bg: "bg-emerald-50/90",
    text: "text-emerald-700",
    border: "border-emerald-200",
    dot: "bg-emerald-500",
  },
  "PARTIALLY MET": {
    bg: "bg-amber-50/90",
    text: "text-amber-700",
    border: "border-amber-200",
    dot: "bg-amber-500",
  },
  MISSING: {
    bg: "bg-red-50/90",
    text: "text-red-700",
    border: "border-red-200",
    dot: "bg-red-500",
  },
  AMBIGUOUS: {
    bg: "bg-purple-50/90",
    text: "text-purple-700",
    border: "border-purple-200",
    dot: "bg-purple-500",
  },
  "NOT VERIFIABLE": {
    bg: "bg-gray-50/90",
    text: "text-gray-600",
    border: "border-gray-200",
    dot: "bg-gray-400",
  },
} as const;

export const motionVariants = {
  page: {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
    exit: { opacity: 0, y: -6, transition: { duration: 0.2 } },
  },
  staggerContainer: {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        staggerChildren: 0.06,
        delayChildren: 0.04,
      },
    },
  },
  staggerItem: {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.32, ease: [0.16, 1, 0.3, 1] } },
  },
  cardHover: {
    rest: { y: 0, scale: 1 },
    hover: { y: -2, scale: 1.008, transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] } },
  },
} as const;
