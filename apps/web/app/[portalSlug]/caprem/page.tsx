import { getHistoriaCaprem } from "@transparencia/db";
import {
  BarChartH,
  CapremActuarialRiskSection,
  CapremEntidadesDonut,
  CapremHeroSection,
  DenseTable,
  fmtCompact,
  fmtCurrency,
  fmtPercent,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

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

  const currentYear = new Date().getFullYear();
  const selectedYear = sParams.ano ? Number(sParams.ano) : currentYear;
  const isCurrentYear = selectedYear === currentYear;
  const _partialPeriod = isCurrentYear
    ? `Janeiro a ${new Date().toLocaleDateString("pt-BR", { month: "long" })} de ${currentYear}`
    : undefined;

  // Consolidado municipal de 100% dos dados previdenciários e assistenciais
  const caprem = await getHistoriaCaprem(portalSlug, selectedYear, null);

  const naturezaCols = [
    {
      header: "Data do Lançamento",
      accessorKey: "dataEmpenho" as const,
      format: "date" as const,
    },
    { header: "Regime / Destino", accessorKey: "destino" as const },
    {
      header: "Elemento / Descrição da Natureza",
      accessorKey: "descricao" as const,
      className: "max-w-sm",
    },
    {
      header: "Empenhado",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  // Agregação dos dados contábeis por destino para o gráfico
  const destinoMap = new Map<string, number>();
  for (const n of caprem.natureza) {
    const key = n.destino;
    destinoMap.set(key, (destinoMap.get(key) || 0) + n.pago);
  }

  const destinoColors: Record<string, string> = {
    "RPPS (CAPREM)": "oklch(0.55 0.14 250)",
    "Aporte Atuarial (CAPREM)": "oklch(0.60 0.18 30)",
    "Amortização Dívida (CAPREM)": "oklch(0.55 0.15 45)",
    "INSS (RGPS)": "oklch(0.65 0.12 180)",
    "Plano de Saúde (CASP)": "oklch(0.60 0.12 210)",
    "Encargo Patronal Geral": "oklch(0.50 0.05 240)",
  };

  const naturezaChartData = Array.from(destinoMap.entries())
    .map(([dest, val]) => ({
      label: dest,
      value: val,
      barColor: destinoColors[dest] || "oklch(0.55 0.11 250)",
    }))
    .sort((a, b) => b.value - a.value);

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
