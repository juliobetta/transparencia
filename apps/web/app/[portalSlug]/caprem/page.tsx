import { getHistoriaCaprem } from "@transparencia/db";
import {
  CapremHeroSection,
  CaspInfoCard,
  DenseTable,
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface CapremPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function CapremPage({
  params,
  searchParams,
}: CapremPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;

  const currentYear = new Date().getFullYear();
  const selectedYear = resolvedSearchParams.ano
    ? Number(resolvedSearchParams.ano)
    : currentYear;
  const entidadesIds = resolvedSearchParams.entidades
    ? resolvedSearchParams.entidades.split(",").filter(Boolean)
    : undefined;

  const isCurrentYear = selectedYear === currentYear;
  const partialPeriod = getPartialYearPeriod();

  const caprem = await getHistoriaCaprem(
    portalSlug,
    selectedYear,
    entidadesIds,
  );

  const entidadesCols = [
    { header: "Entidade / Órgão", accessorKey: "entidade" as const },
    {
      header: "Empenhado (R$)",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Liquidado (R$)",
      accessorKey: "liquidado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago / Repassado (R$)",
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
    { header: "Elemento", accessorKey: "elemento" as const },
    { header: "Descrição da Natureza", accessorKey: "descricao" as const },
    {
      header: "Empenhado (R$)",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago (R$)",
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

      {/* Seção 2: KPIs de Alto Nível */}
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
          title="Índice de Adimplência"
          value={fmtPercent(caprem.taxaExecucao * 100)}
          subtext="% Quitado do Empenhado"
        />
        <KPICard
          title="Aporte Déficit Atuarial"
          value={fmtCompact(caprem.totalAporteAtuarial)}
          subtext="Elemento 97 (Equilíbrio RPPS)"
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

      {/* Seção 4: Decomposição Contábil dos Repasses */}
      {caprem.natureza.length > 0 && (
        <section className="space-y-6 border-t border-[#e7e9ee] pt-8">
          <SectionHeader
            title="Composição Contábil dos Repasses"
            description="Detalhamento das obrigações por elemento de despesa (Contribuições patronais ordinárias, aportes de equilíbrio atuarial e amortização de dívidas)"
          />
          <CaspInfoCard />
          <DenseTable
            data={caprem.natureza}
            columns={naturezaCols}
            searchableKeys={["descricao", "elemento"]}
          />
        </section>
      )}
    </div>
  );
}
