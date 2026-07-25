import type React from "react";
import { cn } from "../utils/cn";

export interface SectionHeaderProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({
  title,
  description,
  action,
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "mb-4 flex flex-wrap items-baseline justify-between gap-2 border-ink border-t-2 pt-3",
        className,
      )}
    >
      <div>
        <h2 className="font-bold font-serif text-ink text-xl tracking-tight">
          {title}
        </h2>
        {description && (
          <p className="mt-0.5 text-subtleText text-xs">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
