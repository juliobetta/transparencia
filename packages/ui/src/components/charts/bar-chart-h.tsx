import { cn } from "../../utils/cn";
import { fmtCurrency } from "../../utils/formatters";

export interface BarChartHItem {
  label: string;
  value: number;
  subtext?: string;
  barColor?: string;
  colorClass?: string;
}

export interface BarChartHProps {
  data: BarChartHItem[];
  maxVal?: number;
  barColor?: string;
}

export function BarChartH({
  data,
  maxVal,
  barColor = "oklch(0.55 0.11 250)",
}: BarChartHProps) {
  const max = maxVal || Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="space-y-3">
      {data.map((item, _idx) => {
        const pct = Math.min(100, Math.max(0, (item.value / max) * 100));
        const itemColor =
          item.barColor || (!item.colorClass ? barColor : undefined);
        return (
          <div key={`bar-chart-h-${item.label}`} className="space-y-1">
            <div className="flex justify-between font-medium text-ink text-xs">
              <span className="max-w-[420px] truncate">{item.label}</span>
              <span className="font-bold font-serif">
                {fmtCurrency(item.value)}
              </span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  item.colorClass,
                )}
                style={{
                  width: `${pct}%`,
                  ...(itemColor ? { backgroundColor: itemColor } : {}),
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
