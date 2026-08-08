import { fmtCompact, toTitleCase } from "@transparencia/ui";

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
        {items
          .sort((a, b) => {
            const pctA = a.empenhado > 0 ? (a.pago / a.empenhado) * 100 : 0;
            const pctB = b.empenhado > 0 ? (b.pago / b.empenhado) * 100 : 0;
            return pctB - pctA;
          })
          .map((item) => {
            const emp = item.empenhado || 0;
            const pag = item.pago || 0;
            const execPct = emp > 0 ? Math.min((pag / emp) * 100, 100) : 0;

            return (
              <div
                key={`${item.descricao}`}
                className="flex items-center justify-between gap-4 text-sm"
              >
                <div className="w-1/2 truncate font-medium text-ink">
                  {toTitleCase(item.descricao)}
                </div>
                <div className="relative flex h-5 flex-1 items-center overflow-hidden rounded-md bg-[#F0F2F5]">
                  <div
                    className="h-full rounded-lg transition-all duration-300"
                    style={{
                      width: `${Math.max(execPct, 2)}%`,
                      backgroundColor: "oklch(0.55 0.11 250)",
                    }}
                  />
                  <span className="absolute right-2 font-semibold text-[10px] text-gray-400">
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
