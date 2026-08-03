import {
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
} from "../utils/formatters";

export interface CapremHeroSectionProps {
  ano: number;
  isCurrentYear: boolean;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  taxaExecucao: number;
  totalAporteAtuarial: number;
  totalDividaResgatada: number;
}

export function CapremHeroSection({
  ano,
  isCurrentYear,
  totalEmpenhado,
  totalLiquidado,
  totalPago,
  taxaExecucao,
  totalAporteAtuarial,
  totalDividaResgatada,
}: CapremHeroSectionProps) {
  const liquidadoRatio =
    totalEmpenhado > 0
      ? Math.min(100, Math.max(0, (totalLiquidado / totalEmpenhado) * 100))
      : 0;
  const pagoRatio =
    totalEmpenhado > 0
      ? Math.min(100, Math.max(0, (totalPago / totalEmpenhado) * 100))
      : 0;

  const partialPeriod = getPartialYearPeriod();

  return (
    <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-12">
      {/* Coluna Esquerda: Narrativa Institucional do RPPS */}
      <div className="space-y-4 lg:col-span-7">
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          TEMAS · PREVIDÊNCIA MUNICIPAL (CAPREM) · {ano}
          {isCurrentYear && partialPeriod ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>

        <h1 className="font-bold font-serif text-3xl text-slate-900 leading-tight tracking-tight sm:text-4xl">
          Garantia do futuro dos servidores:{" "}
          <span className="text-accent">saúde financeira e regularidade</span>{" "}
          nos repasses do RPPS.
        </h1>

        <p className="text-slate-600 text-sm leading-relaxed sm:text-base">
          {isCurrentYear ? (
            <>
              A Prefeitura e os Fundos Municipais de Porciúncula já empenharam{" "}
              <strong className="font-bold text-slate-900">
                {fmtCompact(totalEmpenhado)}
              </strong>{" "}
              em obrigações previdenciárias e aportes ao CAPREM em {ano}. O
              cumprimento rigoroso dos repasses patronais e amortizações
              assegura o pagamento de aposentadorias e pensões aos servidores
              públicos.
            </>
          ) : (
            <>
              No exercício de {ano}, a Prefeitura e os Fundos Municipais
              empenharam{" "}
              <strong className="font-bold text-slate-900">
                {fmtCompact(totalEmpenhado)}
              </strong>{" "}
              em repasses previdenciários ao CAPREM, quitando{" "}
              {fmtPercent(taxaExecucao * 100)} dos compromissos pactuados.
            </>
          )}
        </p>

        {totalAporteAtuarial > 0 && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-900 text-xs sm:text-sm">
            <span className="font-semibold">
              Aporte de Equilíbrio Atuarial:
            </span>{" "}
            Foram alocados {fmtCompact(totalAporteAtuarial)} especificamente
            para a cobertura do déficit atuarial (Elemento 97) visando a
            sustentabilidade do fundo a longo prazo.
          </div>
        )}
      </div>

      {/* Coluna Direita: Card do Fluxo Financeiro (Empenho ao Pagamento) */}
      <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm lg:col-span-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          <span className="font-medium text-slate-500 text-xs">
            Total Empenhado para o CAPREM
          </span>
          <span className="inline-flex shrink-0 items-center rounded-md border border-emerald-200/80 bg-emerald-50 px-2.5 py-0.5 font-medium text-[11px] text-emerald-800">
            Adimplência {fmtPercent(taxaExecucao * 100)}
          </span>
        </div>

        <div className="mb-2 font-bold font-serif text-3xl text-slate-900 tracking-tight sm:text-4xl">
          {fmtCompact(totalEmpenhado)}
        </div>

        <div className="mb-6 space-y-1.5">
          <div className="flex items-center justify-between font-medium text-slate-500 text-xs">
            <span>{fmtCompact(totalPago)} repassados / pagos efetivamente</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
            <div
              className="h-full rounded-md bg-accent transition-all duration-500 ease-out"
              style={{ width: `${pagoRatio}%` }}
            />
          </div>
        </div>

        <div className="border-[#e7e9ee] border-t pt-4">
          <h4 className="mb-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">
            ESTÁGIOS DO REPASSE PREVIDENCIÁRIO
          </h4>
          <div className="space-y-3">
            {/* Liquidado */}
            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span className="font-medium text-slate-900">Liquidado</span>
                <span className="font-semibold text-slate-900">
                  {fmtCompact(totalLiquidado)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
                <div
                  className="h-full rounded-md bg-sky-500 transition-all duration-500"
                  style={{ width: `${liquidadoRatio}%` }}
                />
              </div>
            </div>

            {/* Pago */}
            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span className="font-medium text-slate-900">
                  Pago / Transferido
                </span>
                <span className="font-semibold text-slate-900">
                  {fmtCompact(totalPago)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
                <div
                  className="h-full rounded-md bg-emerald-500 transition-all duration-500"
                  style={{ width: `${pagoRatio}%` }}
                />
              </div>
            </div>

            {totalDividaResgatada > 0 && (
              <div className="pt-2 text-[11px] text-slate-500">
                Inclui {fmtCompact(totalDividaResgatada)} em amortização de
                parcelamentos (Elem. 71).
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
