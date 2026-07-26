import { fmtCompact } from "../../utils/formatters";
import { toTitleCase } from "../../utils/text";

export interface UnidadeGastoItem {
  descricao: string;
  empenhado: number;
  pago: number;
}

export interface UnidadesGastosChartProps {
  items: UnidadeGastoItem[];
  title?: string;
  className?: string;
}

function getNavyGradientColor(ratio: number): string {
  // Interpolate between soft blue/cyan (#6AA8D1) for 0% and deep navy blue (#2B5278) for 100% execution
  const r1 = 0x6a,
    g1 = 0xa8,
    b1 = 0xd1;
  const r2 = 0x2b,
    g2 = 0x52,
    b2 = 0x78;
  const r = Math.round(r1 + (r2 - r1) * ratio);
  const g = Math.round(g1 + (g2 - g1) * ratio);
  const b = Math.round(b1 + (b2 - b1) * ratio);
  return `rgb(${r}, ${g}, ${b})`;
}

export function UnidadesGastosChart({
  items,
  title,
  className = "",
}: UnidadesGastosChartProps) {
  if (!items || items.length === 0) return null;

  return (
    <div
      className={`space-y-4 rounded-2xl border border-borderLine bg-white p-6 ${className}`}
    >
      {title && <h3 className="font-bold text-base text-ink">{title}</h3>}
      <div className="space-y-3">
        {items.map((item) => {
          const emp = item.empenhado || 0;
          const pag = item.pago || 0;
          const execPct = emp > 0 ? Math.min((pag / emp) * 100, 100) : 0;
          const ratio = Math.max(Math.min(execPct / 100, 1), 0);
          const barColor = getNavyGradientColor(ratio);

          return (
            <div
              key={`${item.descricao}`}
              className="flex items-center justify-between gap-4 text-sm"
            >
              <div className="w-1/3 truncate font-medium text-ink">
                {toTitleCase(item.descricao)}
              </div>
              <div className="relative flex h-5 flex-1 items-center overflow-hidden rounded-lg bg-[#F0F2F5]">
                <div
                  className="h-full rounded-lg transition-all duration-300"
                  style={{
                    width: `${Math.max(execPct, 2)}%`,
                    backgroundColor: barColor,
                  }}
                />
                <span className="absolute right-2 font-semibold text-[10px] text-subtleText">
                  {execPct.toFixed(0)}% pago
                </span>
              </div>
              <div className="w-24 shrink-0 text-right font-bold text-ink">
                {fmtCompact(emp)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
