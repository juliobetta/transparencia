import {
  fmtCompact,
  fmtCurrency,
  fmtPercent,
  KPICard,
  toTitleCase,
} from "@transparencia/ui";
import type { Metadata } from "next";
import { BarChartH } from "@/components/bar-chart-h";
import { DonutGastosLocais } from "@/components/donut-gastos-locais";
import { KPIGrid } from "@/components/kpi-grid";
import { RestosAPagarVendorsChart } from "@/components/restos-a-pagar-vendors-chart";
import { SectionHeader } from "@/components/section-header";
import { UnidadesGastosChart } from "@/components/unidades-gastos-chart";
import { createPortalMetadata } from "@/lib/metadata";
import { loadDespesasData } from "./loader";
import { buildDespesasViewModel } from "./view-model";

export const dynamic = "force-dynamic";

interface DespesasPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export async function generateMetadata({
  params,
}: DespesasPageProps): Promise<Metadata> {
  const { portalSlug } = await params;
  return createPortalMetadata("Despesas", portalSlug, {
    description:
      "Análise detalhada das despesas municipais empenhadas, liquidadas e pagas por órgãos, unidades e funções contábeis.",
    path: "/despesas",
    keywords: [
      "despesas municipais",
      "empenhado",
      "liquidado",
      "pago",
      "órgãos públicos",
      "funções contábeis",
    ],
  });
}

export default async function DespesasPage({
  params,
  searchParams,
}: DespesasPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;
  const rawData = await loadDespesasData(portalSlug, resolvedSearchParams);
  const viewModel = buildDespesasViewModel(rawData);

  const {
    selectedYear,
    isCurrentYear,
    partialPeriod,
    metricasGerais,
    impactoLocais,
    restosResumo,
    despesasUnidades,
    diariasResumo,
    diariasBeneficiarios,
    hhiVal,
    hhiStatusText,
  } = viewModel;

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Despesas Detalhadas
        </h1>
        <p className="mt-1 max-w-3xl text-sm text-subtleText leading-relaxed">
          Onde e como os recursos são aplicados: quanto fica na economia local,
          se há concentração em poucos fornecedores e quais compromissos de anos
          anteriores ainda não foram pagos.
        </p>
      </div>

      {/* Grade Hero de 4 KPIs */}
      <KPIGrid columns={4}>
        <KPICard
          title="Total empenhado"
          value={fmtCompact(metricasGerais.empenhado)}
          subtext={`no exercício ${selectedYear}`}
        />
        <KPICard
          title="Total pago"
          value={fmtCompact(metricasGerais.pago)}
          subtext={`no exercício ${selectedYear}`}
        />
        <KPICard
          title="Taxa de quitação"
          value={fmtPercent(metricasGerais.taxaPagamento)}
          subtext={`${fmtCompact(metricasGerais.liquidado)} liquidados`}
        />
        <KPICard
          title="Restos a pagar pendentes"
          value={
            <span className="font-bold text-amber-900">
              {fmtCompact(restosResumo.totalPendente)}
            </span>
          }
          subtext="compromissos de anos anteriores"
        />
      </KPIGrid>

      {/* Seção 1: Para onde vai o dinheiro */}
      <section className="space-y-8">
        <SectionHeader
          title="Para onde vai o dinheiro"
          description="Distribuição das despesas por fornecedores locais e externos, além da concentração de fornecedores."
        />

        <div className="space-y-4">
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
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold font-serif text-ink text-xl">
              Unidades Administrativas
            </h3>
            <span className="font-medium text-subtleText text-xs">
              análise de despesas por unidade do governo
            </span>
          </div>

          {despesasUnidades.length > 0 && (
            <UnidadesGastosChart items={despesasUnidades} />
          )}
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold font-serif text-ink text-xl">
              Diárias e Auxílios de Viagem a Serviço
            </h3>
            <span className="font-medium text-subtleText text-xs">
              gastos com reembolsos de viagem e diárias a servidores
            </span>
          </div>

          <KPIGrid columns={3}>
            <KPICard
              title="Total pago em diárias"
              value={fmtCurrency(diariasResumo.totalValor)}
            />
            <KPICard
              title="Servidores beneficiários"
              value={diariasResumo.totalViajantes}
            />
            <KPICard
              title="Média por viagem"
              value={fmtCurrency(diariasResumo.mediaReembolso)}
            />
          </KPIGrid>

          {diariasBeneficiarios.length > 0 && (
            <div className="space-y-4 rounded-2xl border border-borderLine bg-white p-6">
              <h4 className="font-bold text-ink text-sm">
                Principais servidores beneficiários de diárias
              </h4>
              <BarChartH
                data={diariasBeneficiarios.map((b) => ({
                  label: b.cargo
                    ? `${toTitleCase(b.favorecido)} (${toTitleCase(b.cargo)})`
                    : toTitleCase(b.favorecido),
                  value: b.valor,
                }))}
              />
            </div>
          )}
        </div>
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
