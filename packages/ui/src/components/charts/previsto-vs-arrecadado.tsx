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
  const max =
    maxVal ||
    Math.max(...items.flatMap((item) => [item.previsto, item.arrecadado]), 1);

  return (
    <div className="space-y-6 rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm">
      {items.map((item, idx) => {
        const previstoPct = Math.min(
          100,
          Math.max(0, (item.previsto / max) * 100),
        );
        const arrecadadoPct = Math.min(
          100,
          Math.max(0, (item.arrecadado / max) * 100),
        );

        const formattedPrevisto =
          item.previstoFormatted || `previsto ${fmtCompact(item.previsto)}`;
        const formattedArrecadado =
          item.arrecadadoFormatted ||
          `arrecadado ${fmtCompact(item.arrecadado)}`;

        return (
          <div
            key={`previsto-vs-arrecadado-${item.fonte}`}
            className={idx > 0 ? "border-[#f0f1f4] border-t pt-6" : ""}
          >
            {/* Linha de Cabeçalho do Item */}
            <div className="mb-3 flex items-center justify-between font-medium text-ink text-sm">
              <span className="font-bold text-ink">{item.fonte}</span>
              <span className="font-medium text-subtleText text-xs">
                {Math.round(item.pctRealizado)}% realizado
              </span>
            </div>

            {/* Visual de Barras Duplas (Previsto vs Arrecadado) */}
            <div className="space-y-2">
              {/* Barra de Previsto */}
              <div>
                <div className="h-3.5 w-full overflow-hidden rounded-md bg-[#eef0f4]">
                  <div
                    className="h-full rounded-md bg-[#d5dbe6] transition-all duration-500"
                    style={{ width: `${previstoPct}%` }}
                  />
                </div>
                <div className="mt-1 font-medium text-subtleText text-xs">
                  {formattedPrevisto}
                </div>
              </div>

              {/* Barra de Arrecadado */}
              <div>
                <div className="h-3.5 w-full overflow-hidden rounded-md bg-[#eef0f4]">
                  <div
                    className="h-full rounded-md bg-accent transition-all duration-500"
                    style={{ width: `${arrecadadoPct}%` }}
                  />
                </div>
                <div className="mt-1 text-right font-medium text-subtleText text-xs">
                  {formattedArrecadado}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
