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

export function BarChartH({
  data,
  maxVal,
  barColor = "oklch(0.55 0.11 250)",
}: BarChartHProps) {
  const max = maxVal || Math.max(...data.map((d) => d.value), 1);

  return (
    <div className="space-y-3">
      {data.map((item, idx) => {
        const pct = Math.min(100, Math.max(0, (item.value / max) * 100));
        return (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between font-medium text-ink text-xs">
              <span className="max-w-[240px] truncate">{item.label}</span>
              <span className="font-bold font-serif">
                {fmtCurrency(item.value)}
              </span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-gray-100">
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
