import React from "react";
import { clsx } from "clsx";

export interface BadgeProps {
  variant?: "default" | "accent" | "warning" | "danger" | "success";
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = "default", children, className }: BadgeProps) {
  const styles = {
    default: "bg-gray-100 text-gray-700 border-gray-200",
    accent: "bg-blue-50 text-accent border-blue-200 font-semibold",
    warning: "bg-amber-50 text-amber-800 border-amber-200 font-semibold",
    danger: "bg-rose-50 text-rose-800 border-rose-200 font-semibold",
    success: "bg-emerald-50 text-emerald-800 border-emerald-200 font-semibold",
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-md text-[11px] border font-medium",
        styles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
