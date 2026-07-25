import React from "react";
import { fmtCurrency } from "../../utils/formatters";

export interface BarChartHItem {
  label: string;
  value: number;
  subtext?: string;
}

export interface BarChartHProps {
  data: BarChartHItem[];
  maxVal?: number;
  barColor?: string;
}

export function BarChartH({ data, maxVal, barColor = "oklch(0.55 0.11 250)" }: BarChartHProps) {
  const max = maxVal || Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="space-y-3">
      {data.map((item, idx) => {
        const pct = Math.min(100, Math.max(0, (item.value / max) * 100));
        return (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between text-xs font-medium text-ink">
              <span className="truncate max-w-[240px]">{item.label}</span>
              <span className="font-serif font-bold">{fmtCurrency(item.value)}</span>
            </div>
            <div className="h-3 w-full bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${pct}%`, backgroundColor: barColor }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
