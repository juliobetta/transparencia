import React from "react";
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
        "border-t-2 border-ink pt-3 mb-4 flex items-baseline justify-between flex-wrap gap-2",
        className
      )}
    >
      <div>
        <h2 className="text-xl font-bold font-serif text-ink tracking-tight">
          {title}
        </h2>
        {description && (
          <p className="text-xs text-subtleText mt-0.5">{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
