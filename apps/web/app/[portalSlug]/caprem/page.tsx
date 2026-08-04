import {
  DenseTable,
  fmtCompact,
  fmtCurrency,
  fmtPercent,
  KPICard,
} from "@transparencia/ui";
import { BarChartH } from "@/components/bar-chart-h";
import { CapremActuarialRiskSection } from "@/components/caprem-actuarial-risk-section";
import { CapremEntidadesDonut } from "@/components/caprem-entidades-donut";
import { CapremHeroSection } from "@/components/caprem-hero-section";
import { KPIGrid } from "@/components/kpi-grid";
import { SectionHeader } from "@/components/section-header";
import { loadCapremData } from "./loader";
import { buildCapremViewModel } from "./view-model";

interface CapremPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; empresa?: string }>;
}

export default async function CapremPage({
  params,
  searchParams,
}: CapremPageProps) {
  const { portalSlug } = await params;
  const sParams = await searchParams;
  const rawData = await loadCapremData(portalSlug, sParams);
  const viewModel = buildCapremViewModel(rawData);
  const {
    selectedYear,
    isCurrentYear,
    caprem,
    naturezaCols,
    naturezaChartData,
  } = viewModel;

  return (
    <div className="space-y-12 pb-12">
      {/* Seção 1: Hero Especializado do Tema */}
      <CapremHeroSection
        ano={selectedYear}
        isCurrentYear={isCurrentYear}
        totalEmpenhado={caprem.totalEmpenhado}
        totalLiquidado={caprem.totalLiquidado}
        totalPago={caprem.totalPago}
        taxaExecucao={caprem.taxaExecucao}
        totalAporteAtuarial={caprem.totalAporteAtuarial}
        totalDividaResgatada={caprem.totalDividaResgatada}
      />

      {/* Seção 2: KPIs de Alto Nível (Grid Limpo de 4 Colunas) */}
      <KPIGrid columns={4}>
        <KPICard
          title="Total Empenhado"
          value={fmtCompact(caprem.totalEmpenhado)}
          subtext="Compromissos previdenciários"
          accent
        />
        <KPICard
          title="Total Repassado / Pago"
          value={fmtCompact(caprem.totalPago)}
          subtext="Efetivamente transferido"
        />
        <KPICard
          title="Aporte Déficit Atuarial"
          value={fmtCompact(caprem.totalAporteAtuarial)}
          subtext="Elemento 97 (Equilíbrio RPPS)"
        />
        <KPICard
          title="Índice de Adimplência"
          value={fmtPercent(caprem.taxaExecucao * 100)}
          subtext="% Quitado do Empenhado"
        />
      </KPIGrid>

      {caprem.entidades.length > 0 && (
        <section className="">
          <CapremEntidadesDonut data={caprem.entidades} ano={selectedYear} />
        </section>
      )}

      {/* Seção 3: Diagnóstico de Sustentabilidade Atuarial & Risco Previdenciário */}
      <CapremActuarialRiskSection
        ano={selectedYear}
        risk={caprem.actuarialRisk}
        trend={caprem.actuarialTrend}
        cadprev={caprem.cadprevParcelamentos}
      />

      {/* Seção 5: Composição Contábil dos Repasses (Gráfico Barras + Tabela Paginada) */}
      {caprem.natureza.length > 0 && (
        <section className="space-y-6">
          <SectionHeader
            title="Composição Contábil dos Repasses"
            description="Detalhamento das obrigações por elemento de despesa (Contribuições patronais ordinárias, aportes de equilíbrio atuarial, amortização de dívidas e previdência)"
          />

          {naturezaChartData.length > 0 && (
            <div className="space-y-4 rounded-xl border border-borderLine bg-white p-5">
              <div className="flex items-center justify-between border-gray-100 border-b pb-3">
                <h4 className="font-semibold font-serif text-slate-800 text-sm">
                  Distribuição por Destino Contábil e Regime ({selectedYear})
                </h4>
                <span className="font-medium text-slate-500 text-xs">
                  Total Repassado: {fmtCurrency(caprem.totalPago)}
                </span>
              </div>
              <BarChartH data={naturezaChartData} />
            </div>
          )}

          <div className="space-y-3">
            <h4 className="font-semibold font-serif text-slate-800 text-sm">
              Detalhamento de Lançamentos Contábeis (Paginado)
            </h4>
            <DenseTable
              data={caprem.natureza.map((item) => ({
                ...item,
                descricao: `${item.elemento} - ${item.descricao}`,
              }))}
              columns={naturezaCols}
              searchableKeys={["descricao", "elemento", "destino"]}
              pageSize={10}
            />
          </div>
        </section>
      )}
    </div>
  );
}
