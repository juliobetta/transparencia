import React from "react";
import { clsx } from "clsx";

export interface KPICardProps {
  title: string;
  value: string | number;
  subtext?: string;
  trend?: {
    value: string | number;
    isPositive?: boolean;
  };
  accent?: boolean;
  alert?: boolean;
  className?: string;
}

export function KPICard({
  title,
  value,
  subtext,
  trend,
  accent = false,
  alert = false,
  className,
}: KPICardProps) {
  return (
    <div
      className={clsx(
        "bg-white border border-borderLine rounded-xl p-5 flex flex-col justify-between transition-shadow hover:shadow-sm",
        accent && "border-l-4 border-l-accent",
        alert && "border-l-4 border-l-warning bg-amber-50/20",
        className
      )}
    >
      <div>
        <p className="text-xs font-medium text-subtleText uppercase tracking-wider mb-1">
          {title}
        </p>
        <p
          className={clsx(
            "text-2xl font-bold font-serif leading-tight",
            accent ? "text-accent" : alert ? "text-warning" : "text-ink"
          )}
        >
          {value}
        </p>
      </div>
      {(subtext || trend) && (
        <div className="mt-3 pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-mutedText">
          {subtext && <span>{subtext}</span>}
          {trend && (
            <span
              className={clsx(
                "font-semibold",
                trend.isPositive ? "text-emerald-600" : "text-rose-600"
              )}
            >
              {trend.value}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
