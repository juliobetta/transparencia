import { fmtCompact } from "@transparencia/ui";

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
  // A régua de R$ é definida pelo maior valor (previsto ou arrecadado) entre todas as origens
  const maxScale =
    maxVal ||
    Math.max(...items.flatMap((item) => [item.previsto, item.arrecadado]), 1);

  return (
    <div className="space-y-6 rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm">
      {items.map((item, idx) => {
        // O comprimento da trilha representa o previsto (ou arrecadado se superado), com piso mínimo de 18% para manter legibilidade visual
        const baseVal = Math.max(item.previsto, item.arrecadado);
        const trackWidthPct = Math.min(
          100,
          Math.max(18, (baseVal / maxScale) * 100),
        );

        // Preenchimento interno = proporção arrecadada em relação ao previsto
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
            {/* Linha de Cabeçalho: Nome da Fonte vs Arrecadado / Previsto (fmtCompact já inclui R$) */}
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-bold text-ink">{item.fonte}</span>
              <span className="font-medium text-subtleText text-xs">
                {fmtCompact(item.arrecadado)} / {fmtCompact(item.previsto)}
              </span>
            </div>

            {/* Trilha de fundo (previsto/meta) com largura proporcional à régua de R$ */}
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
