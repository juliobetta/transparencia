export interface SalaryBinItem {
  faixa: string;
  min: number;
  max: number;
  count: number;
}

interface ProventosDistributionChartProps {
  data: SalaryBinItem[];
}

export function ProventosDistributionChart({
  data,
}: ProventosDistributionChartProps) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white p-4 shadow-xs sm:p-6">
      <div className="mb-4">
        <h4 className="font-bold text-lg text-slate-900">
          Distribuição dos Proventos Brutos
        </h4>
        <p className="mt-1 text-slate-500 text-xs">
          O portal não disponibiliza a remuneração líquida individual. O gráfico
          abaixo utiliza os proventos (remuneração bruta) como aproximação.
        </p>
      </div>

      <div className="relative overflow-x-auto overflow-y-hidden pt-2 pb-2">
        <div
          className="grid min-w-[460px] items-end gap-2.5 px-1 pt-2 pb-1 sm:min-w-0"
          style={{
            gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))`,
          }}
        >
          {data.map((item) => {
            const heightPct = Math.min(100, (item.count / maxCount) * 100);
            return (
              <div
                key={item.faixa}
                className="group flex w-full min-w-0 flex-col items-center"
              >
                {/* Count Label */}
                <span className="mb-1 font-bold text-slate-700 text-xs">
                  {item.count}
                </span>

                {/* Bar Container */}
                <div className="relative flex h-44 w-full items-end rounded-t-sm bg-slate-100">
                  <div
                    className="w-full rounded-t-sm bg-sky-600 transition-all duration-500 group-hover:bg-sky-700"
                    style={{ height: `${heightPct}%` }}
                    title={`${item.faixa}: ${item.count} servidores`}
                  />
                </div>

                {/* Range Label */}
                <span
                  className="mt-2 w-full truncate text-center font-medium text-[10px] text-slate-500"
                  title={item.faixa}
                >
                  {item.faixa}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
