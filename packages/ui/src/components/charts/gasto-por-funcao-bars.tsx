import { cn } from "../../utils/cn";
import { fmtCompact } from "../../utils/formatters";

export interface GastoFuncaoItem {
  funcao: string;
  valor: number;
  valorFormatted?: string;
  colorClass?: string;
}

export interface GastoPorFuncaoBarsProps {
  items: GastoFuncaoItem[];
  maxVal?: number;
}

export function GastoPorFuncaoBars({ items, maxVal }: GastoPorFuncaoBarsProps) {
  const max = maxVal || Math.max(...items.map((i) => i.valor), 1);

  const defaultColors = [
    "bg-blue-600",
    "bg-blue-500",
    "bg-sky-500",
    "bg-cyan-500",
    "bg-[#38bdf8]",
    "bg-[#2dd4bf]",
    "bg-[#94a3b8]",
  ];

  return (
    <div className="space-y-4 rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm">
      {items.map((item, idx) => {
        const pct = Math.min(100, Math.max(0, (item.valor / max) * 100));
        const color =
          item.colorClass || defaultColors[idx % defaultColors.length];
        const formattedVal = item.valorFormatted || fmtCompact(item.valor);

        return (
          <div
            key={item.funcao}
            className="flex items-center gap-4 font-medium text-xs"
          >
            <span className="w-32 shrink-0 truncate font-semibold text-ink">
              {item.funcao}
            </span>
            <div className="h-4 flex-1 overflow-hidden rounded-full bg-[#eef0f4]">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-500",
                  color,
                )}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="ml-2 min-w-[80px] shrink-0 text-right font-bold font-serif text-ink text-sm">
              {formattedVal}
            </span>
          </div>
        );
      })}
    </div>
  );
}
