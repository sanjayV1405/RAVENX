"use client";

import React, { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/design-tokens";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
}

export const PrimaryButton = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: "px-3.5 py-1.5 text-xs gap-1.5 rounded-xl",
      md: "px-5 py-2.5 text-xs md:text-sm gap-2 rounded-xl",
      lg: "px-7 py-3.5 text-sm md:text-base gap-2.5 rounded-2xl",
    }[size];

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn("aurora-btn-crimson cursor-pointer", sizeClasses, className)}
        {...props}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!loading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);
PrimaryButton.displayName = "PrimaryButton";

export const SecondaryButton = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const sizeClasses = {
      sm: "px-3.5 py-1.5 text-xs gap-1.5 rounded-xl",
      md: "px-5 py-2.5 text-xs md:text-sm gap-2 rounded-xl",
      lg: "px-7 py-3.5 text-sm md:text-base gap-2.5 rounded-2xl",
    }[size];

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn("aurora-btn-frosted cursor-pointer", sizeClasses, className)}
        {...props}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0 text-gray-500" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        <span>{children}</span>
        {!loading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);
SecondaryButton.displayName = "SecondaryButton";

export const GlassButton = SecondaryButton;

