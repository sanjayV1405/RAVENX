"use client";

import React, { forwardRef } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/design-tokens";

type ButtonVariant = "primary" | "secondary" | "ghost" | "glass" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface PremiumButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "text-white font-semibold shadow-md border-transparent",
  secondary:
    "bg-white text-[#17191F] font-medium border border-[#DDE0E6] hover:bg-[#F5F6F8] shadow-sm",
  ghost:
    "bg-transparent text-[#707582] font-medium border border-transparent hover:bg-black/5",
  glass:
    "font-medium border border-[#DDE0E6] text-[#17191F]",
  danger:
    "bg-red-600 text-white font-semibold border-transparent hover:bg-red-700 shadow-md",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-sm rounded-md gap-1.5",
  md: "px-4 py-2.5 text-sm rounded-lg gap-2",
  lg: "px-6 py-3 text-base rounded-lg gap-2.5",
};

export const PremiumButton = forwardRef<HTMLButtonElement, PremiumButtonProps>(
  (
    {
      variant = "secondary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      className,
      disabled,
      style,
      ...props
    },
    ref
  ) => {
    const isPrimary = variant === "primary";
    const isGlass = variant === "glass";

    const baseClass = cn(
      "inline-flex items-center justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed select-none",
      variantStyles[variant],
      sizeStyles[size],
      className
    );

    const primaryStyle =
      isPrimary
        ? {
            background: "linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)",
            boxShadow: "0 2px 8px rgba(220,38,38,0.28)",
            ...style,
          }
        : isGlass
        ? {
            background: "rgba(255,255,255,0.68)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
            ...style,
          }
        : style;

    return (
      <motion.button
        ref={ref}
        whileTap={!disabled && !loading ? { scale: 0.97 } : undefined}
        whileHover={
          isPrimary && !disabled && !loading
            ? { y: -1, boxShadow: "0 4px 16px rgba(220,38,38,0.38)" }
            : undefined
        }
        className={baseClass}
        style={primaryStyle}
        disabled={disabled || loading}
        {...(props as React.ComponentProps<typeof motion.button>)}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          leftIcon
        )}
        {children}
        {!loading && rightIcon}
      </motion.button>
    );
  }
);

PremiumButton.displayName = "PremiumButton";
export default PremiumButton;

