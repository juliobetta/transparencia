import { fmtCompact } from "../../utils/formatters";

export interface PrevistoVsArrecadadoItem {
  fonte: string;
  previsto: number;
  arrecadado: number;
  pctRealizado: number;
  previstoFormatted?: string;
  arrecadadoFormatted?: string;
}

export interface PrevistoVsArrecadadoProps {
  items: PrevistoVsArrecadadoItem[];
  maxVal?: number;
}

export function PrevistoVsArrecadadoOrigem({
  items,
  maxVal,
}: PrevistoVsArrecadadoProps) {
  // A régua de R$ é definida pelo maior previsto entre todas as origens (ou maxVal se informado)
  const maxPrevisto =
    maxVal || Math.max(...items.map((item) => item.previsto), 1);

  return (
    <div className="space-y-6 rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm">
      {items.map((item, idx) => {
        // Comprimento da trilha de fundo = proporção do previsto em relação ao maior previsto
        const trackWidthPct = Math.min(
          100,
          Math.max(5, (item.previsto / maxPrevisto) * 100),
        );

        // Preenchimento interno = arrecadado em relação ao previsto desta própria fonte
        const fillPct =
          item.previsto > 0
            ? Math.min(
                100,
                Math.max(0, (item.arrecadado / item.previsto) * 100),
              )
            : 0;

        const falta = Math.max(0, item.previsto - item.arrecadado);
        const faltaText = falta > 0 ? ` · faltam ${fmtCompact(falta)}` : "";

        const isPropria =
          item.fonte.toLowerCase().includes("própria") ||
          item.fonte.toLowerCase().includes("propria");

        const barColorClass = isPropria ? "bg-[#3c914e]" : "bg-[#3775b3]";

        return (
          <div
            key={`previsto-vs-arrecadado-${item.fonte}`}
            className={idx > 0 ? "pt-2" : ""}
          >
            {/* Linha de Cabeçalho: Nome da Fonte vs R$ Arrecadado / Previsto */}
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-bold text-ink">{item.fonte}</span>
              <span className="font-medium text-subtleText text-xs">
                R$ {fmtCompact(item.arrecadado)} / {fmtCompact(item.previsto)}
              </span>
            </div>

            {/* Trilha de fundo (previsto) com largura proporcional à régua de R$ */}
            <div className="w-full">
              <div
                className="h-5 overflow-hidden rounded-md bg-[#eef0f4]"
                style={{ width: `${trackWidthPct}%` }}
              >
                <div
                  className={`h-full rounded-md ${barColorClass} transition-all duration-500`}
                  style={{ width: `${fillPct}%` }}
                />
              </div>
            </div>

            {/* Subtexto: % realizado · faltam R$ X */}
            <div className="mt-1 font-medium text-subtleText text-xs">
              {Math.round(item.pctRealizado)}% realizado{faltaText}
            </div>
          </div>
        );
      })}
    </div>
  );
}
