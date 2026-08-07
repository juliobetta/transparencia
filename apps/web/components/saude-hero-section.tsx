import { fmtCompact, fmtPercent } from "@transparencia/ui";

export interface SaudeHeroOrcamentoProps {
  dotacao: number;
  empenhado: number;
  liquidado: number;
  pago: number;
  taxaExecucao: number;
  medicamentosInsumos: number;
  contratosVinculadosCount: number;
  fornecedoresAtivosCount: number;
}

export interface SaudeHeroFontesProps {
  uniaoSusPct: number;
  estadoPct: number;
  propriaPct: number;
  repassesPrefeitura: number;
  emendasParlamentares: number;
}

export interface SaudeHeroSectionProps {
  ano: number;
  isCurrentYear: boolean;
  partialPeriod: string;
  orcamento: SaudeHeroOrcamentoProps;
  fontesReceita: SaudeHeroFontesProps;
}

export function SaudeHeroSection({
  ano,
  isCurrentYear,
  partialPeriod,
  orcamento,
  fontesReceita,
}: SaudeHeroSectionProps) {
  const susPct = fontesReceita.uniaoSusPct ?? 0;

  const empenhadoRatio =
    orcamento.dotacao > 0
      ? Math.min(
          100,
          Math.max(0, (orcamento.empenhado / orcamento.dotacao) * 100),
        )
      : 0;

  const liquidadoRatio =
    orcamento.empenhado > 0
      ? Math.min(
          100,
          Math.max(0, (orcamento.liquidado / orcamento.empenhado) * 100),
        )
      : 0;

  const pagoRatio =
    orcamento.empenhado > 0
      ? Math.min(100, Math.max(0, (orcamento.pago / orcamento.empenhado) * 100))
      : 0;

  const insumosRatio =
    orcamento.empenhado > 0
      ? Math.min(
          100,
          Math.max(
            0,
            (orcamento.medicamentosInsumos / orcamento.empenhado) * 100,
          ),
        )
      : 0;

  return (
    <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-12">
      {/* Coluna Esquerda: Narrativa */}
      <div className="space-y-4 lg:col-span-7">
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          TEMAS · FUNDO MUNICIPAL DE SAÚDE · {ano}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>

        <h1 className="font-bold font-serif text-3xl text-slate-900 leading-tight tracking-tight sm:text-4xl">
          {susPct} de cada R$ 100 da saúde vêm do SUS.{" "}
          <span className="text-accent">O que o município faz com eles</span> se
          decide na forma de contratar.
        </h1>

        <p className="text-slate-600 text-sm leading-relaxed sm:text-base">
          {isCurrentYear ? (
            <>
              O Fundo Municipal de Saúde já empenhou{" "}
              <strong className="font-bold text-slate-900">
                {fmtCompact(orcamento.empenhado)}
              </strong>{" "}
              em {ano} — {fmtPercent(orcamento.taxaExecucao * 100)} da dotação
              aprovada. Com a destinação de recursos oriundos do SUS e repasses
              governamentais, a transparência e a eficiência de cada contrato de
              insumos, exames e serviços garantem que a atenção básica chegue a
              quem precisa.
            </>
          ) : (
            <>
              O Fundo Municipal de Saúde empenhou{" "}
              <strong className="font-bold text-slate-900">
                {fmtCompact(orcamento.empenhado)}
              </strong>{" "}
              no exercício de {ano} — {fmtPercent(orcamento.taxaExecucao * 100)}{" "}
              da dotação aprovada. Dos recursos oriundos do SUS e repasses
              governamentais, a execução de cada contrato de insumos, exames e
              serviços definiu a cobertura da atenção básica no município
              naquele ano.
            </>
          )}
        </p>
      </div>

      {/* Coluna Direita: Card Visual do Empenho ao Pagamento */}
      <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm lg:col-span-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          {isCurrentYear ? (
            <>
              <span className="font-medium text-slate-500 text-xs">
                Empenhado no ano até agora
              </span>
              <span className="inline-flex shrink-0 items-center rounded-md border border-emerald-200/80 bg-emerald-50 px-2.5 py-0.5 font-medium text-[11px] text-emerald-800">
                no ritmo
              </span>
            </>
          ) : (
            <span className="font-medium text-slate-500 text-xs">
              Empenhado no exercício
            </span>
          )}
        </div>

        <div className="mb-2 font-bold font-serif text-3xl text-slate-900 tracking-tight sm:text-4xl">
          {fmtCompact(orcamento.empenhado)}
        </div>

        <div className="mb-6 space-y-1.5">
          <div className="flex items-center justify-between font-medium text-slate-500 text-xs">
            <span>
              {fmtPercent(orcamento.taxaExecucao * 100)} da dotação de{" "}
              {fmtCompact(orcamento.dotacao)}
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
            <div
              className="h-full rounded-md bg-accent transition-all duration-500 ease-out"
              style={{ width: `${empenhadoRatio}%` }}
            />
          </div>
        </div>

        <div className="border-[#e7e9ee] border-t pt-4">
          <h4 className="mb-3 font-semibold text-slate-500 text-xs uppercase tracking-wider">
            DO EMPENHO ATÉ O PAGAMENTO
          </h4>
          <div className="space-y-3">
            {/* Liquidado */}
            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span className="font-medium text-slate-900">Liquidado</span>
                <span className="font-semibold text-slate-900">
                  {fmtCompact(orcamento.liquidado)}
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
                <span className="font-medium text-slate-900">Pago</span>
                <span className="font-semibold text-slate-900">
                  {fmtCompact(orcamento.pago)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
                <div
                  className="h-full rounded-md bg-accent transition-all duration-500"
                  style={{ width: `${pagoRatio}%` }}
                />
              </div>
            </div>

            {/* Medicamentos e insumos */}
            <div className="space-y-1 text-xs">
              <div className="flex items-center justify-between text-slate-600">
                <span className="font-medium text-slate-900">
                  Medicamentos e insumos
                </span>
                <span className="font-semibold text-slate-900">
                  {fmtCompact(orcamento.medicamentosInsumos)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
                <div
                  className="h-full rounded-md bg-emerald-500 transition-all duration-500"
                  style={{ width: `${insumosRatio}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
