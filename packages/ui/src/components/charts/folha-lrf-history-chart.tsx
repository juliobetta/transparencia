export interface FolhaHistoryItem {
  ano: number;
  percentualFolha: number;
  isCurrentYear?: boolean;
}

export interface FolhaLrfHistoryChartProps {
  data: FolhaHistoryItem[];
}

export function FolhaLrfHistoryChart({ data }: FolhaLrfHistoryChartProps) {
  const maxPercent = 60; // Max scale for chart height

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-lg text-slate-900">
            Folha como % da receita, ano a ano
          </h3>
        </div>
        <span className="font-medium text-slate-500 text-xs">
          com os limites da LRF
        </span>
      </div>

      <div className="relative pt-8 pb-4">
        {/* Horizontal Threshold Lines */}
        <div className="pointer-events-none absolute inset-x-0 top-8 bottom-12 flex flex-col justify-between">
          {/* Legal 54% */}
          <div className="relative w-full border-red-400 border-t border-solid">
            <span className="absolute -top-2.5 right-0 bg-white px-1 font-semibold text-[11px] text-red-600">
              legal 54%
            </span>
          </div>

          {/* Prudencial 51.3% */}
          <div className="relative w-full border-orange-400 border-t border-dashed">
            <span className="absolute -top-2.5 right-0 bg-white px-1 font-semibold text-[11px] text-orange-600">
              prudencial 51,3%
            </span>
          </div>

          {/* Alerta 48.6% */}
          <div className="relative w-full border-yellow-500 border-t border-dotted">
            <span className="absolute -top-2.5 right-0 bg-white px-1 font-semibold text-[11px] text-yellow-700">
              alerta 48,6%
            </span>
          </div>
        </div>

        {/* Bars Container */}
        <div className="relative z-10 flex h-56 items-end justify-around pt-6">
          {data.map((item) => {
            const heightPct = Math.min(
              100,
              (item.percentualFolha / maxPercent) * 100,
            );
            return (
              <div
                key={item.ano}
                className="group flex w-16 flex-col items-center"
              >
                {/* Bar Label */}
                <span className="mb-2 font-bold text-slate-800 text-xs">
                  {item.percentualFolha.toFixed(1).replace(".", ",")}%
                </span>

                {/* Bar */}
                <div className="relative flex h-44 w-12 items-end rounded-t-md bg-slate-100">
                  <div
                    className={`w-full rounded-t-md transition-all duration-500 ${
                      item.percentualFolha > 54
                        ? "bg-red-500"
                        : item.percentualFolha > 51.3
                          ? "bg-orange-500"
                          : "bg-sky-600"
                    }`}
                    style={{ height: `${heightPct}%` }}
                  />
                </div>

                {/* Year Label */}
                <span className="mt-3 font-medium text-slate-500 text-xs">
                  {item.ano}
                  {item.isCurrentYear ? "*" : ""}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
