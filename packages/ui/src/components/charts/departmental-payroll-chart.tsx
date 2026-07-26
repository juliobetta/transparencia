import { fmtCompact } from "../../utils/formatters";

export interface DepartmentalItem {
  descricao: string;
  pago: number;
}

interface DepartmentalPayrollChartProps {
  data: DepartmentalItem[];
  selectedYear: number;
}

export function DepartmentalPayrollChart({
  data,
  selectedYear,
}: DepartmentalPayrollChartProps) {
  const maxPaid = Math.max(...data.map((d) => d.pago), 1);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-bold font-serif text-slate-900 text-xl">
          Pagamentos via Responsáveis de Secretaria
        </h2>
      </div>

      {/* Info Callout Box */}
      <div className="rounded-xl border border-sky-200 bg-sky-50/60 p-5 text-sky-900">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 font-bold text-base text-sky-600">ℹ</div>
          <div className="space-y-2 text-xs leading-relaxed">
            <h4 className="font-semibold text-slate-900 text-sm">
              Por que uma pessoa aparece recebendo milhões de reais?
            </h4>
            <p className="text-slate-700">
              No Brasil, é prática comum em municípios que o ordenador de
              despesas de cada secretaria (o responsável pelo departamento)
              receba o montante total da folha de pagamento em seu CPF e o
              distribua entre os servidores da unidade. O sufixo{" "}
              <strong className="font-semibold text-slate-900">
                &quot;E OUTROS&quot;
              </strong>{" "}
              no nome indica exatamente isso: o valor não é de uso pessoal —
              representa salários de toda a equipe.
            </p>
            <p className="font-medium text-slate-600">
              Esses pagamentos são excluídos da análise de Fornecedores e
              Compras Locais para não distorcer os índices de concentração e
              compras locais.
            </p>
          </div>
        </div>
      </div>

      {/* Bar Chart Container */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-6 font-bold text-base text-slate-900">
          Folha distribuída por responsável ({selectedYear})
        </h3>

        {data.length === 0 ? (
          <p className="py-6 text-center text-slate-500 text-sm">
            Nenhum pagamento registrado nesta categoria para este exercício.
          </p>
        ) : (
          <div className="space-y-4">
            {data.map((item) => {
              const widthPct = Math.min(100, (item.pago / maxPaid) * 100);
              return (
                <div key={item.descricao} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="max-w-xl truncate font-medium text-slate-800">
                      {item.descricao}
                    </span>
                    <span className="ml-2 font-bold text-slate-900">
                      {fmtCompact(item.pago)}
                    </span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-md bg-slate-100">
                    <div
                      className="h-full rounded-md bg-sky-600 transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
