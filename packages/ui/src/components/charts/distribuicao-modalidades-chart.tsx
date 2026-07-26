"use client";

import { cn } from "../../utils/cn";
import { toTitleCase } from "../../utils/text";

export interface ItemDistribucaoModalidadeUI {
  modalidade: string;
  valorTotal: number;
  quantidade: number;
  pctValor?: number;
}

export interface DistribucaoModalidadesChartProps {
  data: ItemDistribucaoModalidadeUI[];
  className?: string;
}

const MODALITY_COLORS: Record<string, string> = {
  "pregão eletrônico": "bg-[#3182ce]",
  "pregao eletronico": "bg-[#3182ce]",
  "pregão presencial": "bg-[#3182ce]",
  "pregao presencial": "bg-[#3182ce]",
  concorrência: "bg-[#4299e1]",
  concorrencia: "bg-[#4299e1]",
  dispensa: "bg-[#319795]",
  "adesão a ata": "bg-[#38b2ac]",
  "adesao a ata": "bg-[#38b2ac]",
  inexigibilidade: "bg-[#4fd1c5]",
};

const DEFAULT_COLOR_PALETTE = [
  "bg-[#3182ce]",
  "bg-[#4299e1]",
  "bg-[#319795]",
  "bg-[#38b2ac]",
  "bg-[#4fd1c5]",
  "bg-[#718096]",
];

export function fmtCompactMi(value: number): string {
  if (value >= 1_000_000) {
    const mi = (value / 1_000_000).toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return `R$ ${mi}mi`;
  }
  if (value >= 1_000) {
    const mil = (value / 1_000).toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
    return `R$ ${mil}mil`;
  }
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  });
}

export function DistribucaoModalidadesChart({
  data,
  className,
}: DistribucaoModalidadesChartProps) {
  const maxVal = Math.max(...data.map((d) => d.valorTotal), 1);

  return (
    <div className={cn("space-y-4", className)}>
      {data.map((item, idx) => {
        const pct = Math.min(
          100,
          Math.max(2, (item.valorTotal / maxVal) * 100),
        );
        const keyLower = item.modalidade.toLowerCase().trim();
        const colorClass =
          MODALITY_COLORS[keyLower] ||
          DEFAULT_COLOR_PALETTE[idx % DEFAULT_COLOR_PALETTE.length];

        return (
          <div
            key={`modalidade-${item.modalidade}`}
            className="flex items-center gap-4 font-medium text-slate-700 text-xs"
          >
            {/* Left label */}
            <span className="w-36 shrink-0 truncate font-medium text-slate-700">
              {toTitleCase(item.modalidade)}
            </span>

            {/* Bar track & fill */}
            <div className="h-7 w-full overflow-hidden rounded-md">
              <div
                className={cn(
                  "h-full rounded-md transition-all duration-500",
                  colorClass,
                )}
                style={{ width: `${pct}%` }}
              />
            </div>

            {/* Right value */}
            <div className="w-36 shrink-0 text-right font-normal text-slate-500">
              <span>{fmtCompactMi(item.valorTotal)}</span>
              <span className="mx-1 text-slate-300">·</span>
              <span className="font-bold text-slate-900">
                {item.quantidade}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
