import { cn } from "@transparencia/ui";
import type React from "react";

export interface SectionHeaderProps {
  title?: string;
  children?: React.ReactNode;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  children,
  description,
  action,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "mb-4 flex flex-wrap items-baseline justify-between gap-2 border-ink border-t-2 pt-8",
        className,
      )}
    >
      <div>
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          {children || title}
        </h2>
        {description && (
          <p className="mt-0.5 text-subtleText text-xs">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
