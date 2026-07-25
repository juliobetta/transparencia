import { getHistoriaCaprem } from "@transparencia/db";
import { KPICard, KPIGrid, SectionHeader, DenseTable, fmtCompact, fmtCurrency } from "@transparencia/ui";

export const dynamic = "force-dynamic";

export default async function CapremPage() {
  const currentYear = 2025;
  const caprem = await getHistoriaCaprem(currentYear);

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
      header: "Pago (R$)",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold font-serif text-ink">Painel CAPREM</h1>
        <p className="text-sm text-subtleText mt-1">
          Acompanhamento dos repasses previdenciários e obrigações com a Caixa de Aposentadoria e Pensões ({currentYear})
        </p>
      </div>

      <KPIGrid columns={3}>
        <KPICard title="Total Empenhado" value={fmtCompact(caprem.total_empenhado)} subtext="Compromissos previdenciários" accent />
        <KPICard title="Total Liquidado" value={fmtCompact(caprem.total_liquidado)} subtext="Atestado pelos órgãos" />
        <KPICard title="Total Repassado/Pago" value={fmtCompact(caprem.total_pago)} subtext="Efetivamente transferido" />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Repasses por Entidade ao CAPREM"
          description="Valores empenhados e repassados por órgão da administração municipal ao regime de previdência"
        />
        <DenseTable data={caprem.entidades} columns={entidadesCols} searchableKeys={["entidade"]} />
      </div>
    </div>
  );
}
