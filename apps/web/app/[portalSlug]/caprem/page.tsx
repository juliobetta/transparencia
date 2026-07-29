import { getHistoriaCaprem } from "@transparencia/db";
import {
  CapremHeroSection,
  DenseTable,
  fmtCompact,
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
  const partialPeriod = isCurrentYear
    ? `Janeiro a ${new Date().toLocaleDateString("pt-BR", { month: "long" })} de ${currentYear}`
    : undefined;

  // Consolidado municipal de 100% dos dados previdenciários e assistenciais
  const caprem = await getHistoriaCaprem(portalSlug, selectedYear, null);

  const entidadesCols = [
    { header: "Órgão / Entidade", accessorKey: "entidade" as const },
    {
      header: "Empenhado",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Liquidado",
      accessorKey: "liquidado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Adimplência",
      accessorKey: "taxaExecucao" as const,
      align: "right" as const,
      format: "percent" as const,
    },
  ];

  const naturezaCols = [
    {
      header: "Data do Lançamento",
      accessorKey: "dataEmpenho" as const,
      format: "date" as const,
    },
    { header: "Destino", accessorKey: "destino" as const },
    {
      header: "Elemento / Descrição da Natureza",
      accessorKey: "descricao" as const,
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

  return (
    <div className="space-y-12 pb-12">
      {/* Seção 1: Hero Especializado do Tema */}
      <CapremHeroSection
        ano={selectedYear}
        isCurrentYear={isCurrentYear}
        partialPeriod={partialPeriod}
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

      {/* Seção 3: Repasses por Entidade / Órgão */}
      <section className="space-y-4">
        <SectionHeader
          title="Repasses por Entidade ao CAPREM"
          description="Valores empenhados, liquidados e pagos por cada órgão da administração municipal ao regime previdenciário"
        />
        <DenseTable
          data={caprem.entidades}
          columns={entidadesCols}
          searchableKeys={["entidade"]}
        />
      </section>

      {/* Seção 5: Decomposição Contábil dos Repasses */}
      {caprem.natureza.length > 0 && (
        <section className="space-y-4">
          <SectionHeader
            title="Composição Contábil dos Repasses"
            description="Detalhamento das obrigações por elemento de despesa (Contribuições patronais ordinárias, aportes de equilíbrio atuarial, amortização de dívidas e plano de saúde)"
          />
          <DenseTable
            data={caprem.natureza.map((item) => ({
              ...item,
              descricao: `${item.elemento} - ${item.descricao}`,
            }))}
            columns={naturezaCols}
            searchableKeys={["descricao", "elemento", "destino"]}
          />
        </section>
      )}
    </div>
  );
}
