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
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="font-bold text-lg text-slate-900">
          Distribuição dos Proventos Brutos
        </h3>
        <p className="mt-1 text-slate-500 text-xs">
          O portal não disponibiliza a remuneração líquida individual. O gráfico
          abaixo utiliza os proventos (remuneração bruta) como aproximação.
        </p>
      </div>

      <div className="relative pt-6 pb-2">
        <div className="flex h-56 items-end justify-between gap-2 px-2 pt-6">
          {data.map((item) => {
            const heightPct = Math.min(100, (item.count / maxCount) * 100);
            return (
              <div
                key={item.faixa}
                className="group flex flex-1 flex-col items-center"
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
                <span className="mt-2 max-w-full truncate text-center font-medium text-[10px] text-slate-500">
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
