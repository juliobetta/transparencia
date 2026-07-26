import {
  getConcentracaoFornecedores,
  getDespesasPorUnidade,
  getImpactoGastosLocais,
  getPortalConfig,
  getRestosAPagarResumo,
} from "@transparencia/db";
import {
  DonutGastosLocais,
  fmtCompact,
  fmtPercent,
  KPICard,
  KPIGrid,
  RestosAPagarVendorsChart,
  UnidadesGastosChart,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface DespesasPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function DespesasPage({
  params,
  searchParams,
}: DespesasPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;

  const currentYear = new Date().getFullYear();
  const selectedYear = resolvedSearchParams.ano
    ? Number(resolvedSearchParams.ano)
    : currentYear;
  const entidadesIds = resolvedSearchParams.entidades
    ? resolvedSearchParams.entidades.split(",").filter(Boolean)
    : undefined;

  const portalConfig = await getPortalConfig();

  // Query DB data
  const impactoLocais = await getImpactoGastosLocais({
    year: selectedYear,
    empresaIds: entidadesIds,
    cidadeClean: portalConfig?.cidadeClean || "",
    portalSlug,
  });
  const concentracao = await getConcentracaoFornecedores(
    selectedYear,
    entidadesIds,
  );
  const restosResumo = await getRestosAPagarResumo(selectedYear, entidadesIds);
  const despesasUnidades = await getDespesasPorUnidade(
    selectedYear,
    entidadesIds,
  );

  // HHI text status
  const hhiVal = Math.round(concentracao.hhi || 0);
  const hhiStatusText =
    hhiVal <= 1500
      ? "baixa · abaixo de 1.500"
      : hhiVal <= 2500
        ? "moderada · abaixo de 2.500"
        : "alta · acima de 2.500";

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Despesas Detalhadas
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-subtleText leading-relaxed">
          Onde e como os recursos são aplicados: quanto fica na economia local,
          se há concentração em poucos fornecedores e quais compromissos de anos
          anteriores ainda não foram pagos.
        </p>
      </div>

      <hr className="border-borderLine" />

      {/* Seção 1: Para onde vai o dinheiro */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-bold font-serif text-2xl text-ink">
            Para onde vai o dinheiro
          </h2>
        </div>

        <div className="flex items-center justify-between">
          <h3 className="font-bold font-serif text-ink text-xl">
            Fornecedores e gastos locais
          </h3>
          <span className="font-medium text-subtleText text-xs">
            apenas compras, materiais, serviços e equipamentos
          </span>
        </div>

        <div className="grid grid-cols-1 items-stretch gap-6 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <DonutGastosLocais
              localValor={impactoLocais.localPago}
              externoValor={impactoLocais.externoPago}
              pctLocal={impactoLocais.pctLocal}
              className="h-full"
            />
          </div>

          <div className="flex flex-col justify-between gap-4 lg:col-span-5">
            <KPICard
              title="Índice de compras locais"
              value={fmtPercent(impactoLocais.pctLocal)}
              subtext={
                impactoLocais.historicoPctLocal
                  ? `dos recursos em ${selectedYear} (${fmtPercent(impactoLocais.historicoPctLocal)} no acumulado histórico)`
                  : ""
              }
              className="flex-1 justify-center"
            />

            <KPICard
              title="HHI — concentração de fornecedores"
              value={hhiVal.toLocaleString("pt-BR")}
              subtext={hhiStatusText}
              className="flex-1 justify-center"
            />
          </div>
        </div>

        <hr className="border-borderLine" />

        <div className="flex items-center justify-between">
          <h3 className="font-bold font-serif text-ink text-xl">
            Unidades Administrativas
          </h3>
          <span className="font-medium text-subtleText text-xs">
            análise de despesas por unidade do governo
          </span>
        </div>

        {despesasUnidades.length > 0 && (
          <UnidadesGastosChart items={despesasUnidades.slice(0, 10)} />
        )}
      </section>

      <hr className="border-[#1a1d21] border-t-2" />

      {/* Seção 2: Restos a pagar */}
      <section className="space-y-4">
        <div>
          <h2 className="font-bold font-serif text-2xl text-ink">
            Restos a pagar
          </h2>
        </div>

        {/* Banner Informativo */}
        <div className="rounded-xl border-[#2B5278] border-l-4 bg-[#F0F6FD] p-4 text-[#1B3A5A] text-sm leading-relaxed">
          São despesas empenhadas em anos anteriores ainda não pagas —
          compromissos legais que continuam válidos até serem quitados ou
          cancelados.
        </div>

        {/* 3 KPI Grid */}
        <KPIGrid columns={3}>
          <KPICard
            title="Total pendente"
            value={
              <span className="font-bold text-amber-900">
                {fmtCompact(restosResumo.totalPendente)}
              </span>
            }
          />
          <KPICard
            title="Fornecedores aguardando"
            value={restosResumo.fornecedoresAguardando}
          />
          <KPICard
            title="Dívida mais antiga desde"
            value={restosResumo.dividaMaisAntigaAno}
          />
        </KPIGrid>

        {/* Ranking Fornecedores com maior pendência */}
        {restosResumo.topFornecedores.length > 0 && (
          <RestosAPagarVendorsChart items={restosResumo.topFornecedores} />
        )}
      </section>
    </div>
  );
}
