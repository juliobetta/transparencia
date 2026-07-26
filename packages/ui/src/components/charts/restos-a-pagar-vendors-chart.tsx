import { fmtCompact } from "../../utils/formatters";
import { toTitleCase } from "../../utils/text";

export interface RestosAPagarVendorItem {
  fornecedor: string;
  valor: number;
}

export interface RestosAPagarVendorsChartProps {
  items: RestosAPagarVendorItem[];
  title?: string;
  className?: string;
}

function getTerracottaGradientColor(ratio: number): string {
  // Interpolate between soft amber/terracotta (#D99373) for low values and dark terracotta (#A85348) for 100% max value
  const r1 = 0xd9,
    g1 = 0x93,
    b1 = 0x73;
  const r2 = 0xa8,
    g2 = 0x53,
    b2 = 0x48;
  const r = Math.round(r1 + (r2 - r1) * ratio);
  const g = Math.round(g1 + (g2 - g1) * ratio);
  const b = Math.round(b1 + (b2 - b1) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
}

export function RestosAPagarVendorsChart({
  items,
  title = "Fornecedores com maior pendência",
  className = "",
}: RestosAPagarVendorsChartProps) {
  if (!items || items.length === 0) return null;

  const maxVal = Math.max(...items.map((i) => i.valor), 1);

  return (
    <div
      className={`space-y-4 rounded-2xl border border-borderLine bg-white p-6 ${className}`}
    >
      {title && <h3 className="font-bold text-base text-ink">{title}</h3>}
      <div className="space-y-3">
        {items.map((item) => {
          const ratio = Math.max(Math.min(item.valor / maxVal, 1), 0);
          const barWidthPct = Math.max(ratio * 100, 5);
          const barColor = getTerracottaGradientColor(ratio);

          return (
            <div
              key={item.fornecedor}
              className="flex items-center justify-between gap-4 text-sm"
            >
              <div className="w-1/3 truncate font-medium text-ink">
                {toTitleCase(item.fornecedor)}
              </div>
              <div className="flex h-5 flex-1 items-center overflow-hidden rounded-lg">
                <div
                  className="h-full rounded-lg transition-all duration-300"
                  style={{
                    width: `${barWidthPct}%`,
                    backgroundColor: barColor,
                  }}
                />
              </div>
              <div className="w-24 shrink-0 text-right font-bold text-ink">
                {fmtCompact(item.valor)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
