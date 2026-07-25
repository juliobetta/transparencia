import { cn } from "../utils/cn";

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
      className={cn(
        "flex flex-col justify-between rounded-xl border border-borderLine bg-white p-5 transition-shadow hover:shadow-sm",
        accent && "border-l-4 border-l-accent",
        alert && "border-l-4 border-l-warning bg-amber-50/20",
        className,
      )}
    >
      <div>
        <p className="mb-1 font-medium text-subtleText text-xs uppercase tracking-wider">
          {title}
        </p>
        <p
          className={cn(
            "font-bold font-serif text-2xl leading-tight",
            accent ? "text-accent" : alert ? "text-warning" : "text-ink",
          )}
        >
          {value}
        </p>
      </div>
      {(subtext || trend) && (
        <div className="mt-3 flex items-center justify-between border-gray-100 border-t pt-2 text-mutedText text-xs">
          {subtext && <span>{subtext}</span>}
          {trend && (
            <span
              className={cn(
                "font-semibold",
                trend.isPositive ? "text-emerald-600" : "text-rose-600",
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
