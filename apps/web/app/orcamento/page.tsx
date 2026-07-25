import {
  getExecucaoOrcamentaria,
  getOrcamentoFuncional,
  summarizeExecucao,
} from "@transparencia/db";
import {
  DenseTable,
  FunnelWaterfall,
  fmtCompact,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

export default async function OrcamentoPage() {
  const currentYear = 2025;
  const items = await getExecucaoOrcamentaria(currentYear);
  const summary = summarizeExecucao(items);
  const _funcional = await getOrcamentoFuncional(currentYear);

  const funnelData = [
    { name: "Dotação Atualizada", value: summary.total_dotacao },
    { name: "Empenhado", value: summary.total_empenhado },
    { name: "Liquidado", value: summary.total_liquidado },
    { name: "Pago", value: summary.total_pago },
  ];

  const orgaosCols = [
    { header: "Código", accessorKey: "codigo" as const },
    { header: "Órgão / Unidade", accessorKey: "descricao" as const },
    {
      header: "Dotação (R$)",
      accessorKey: "dotacao_atualizada" as const,
      align: "right" as const,
      format: "currency" as const,
    },
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
    {
      header: "Execução",
      accessorKey: "alerta" as const,
      align: "center" as const,
      format: "statusBadge" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Execução Orçamentária
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Acompanhamento do funil orçamentário por órgãos e funções de governo (
          {currentYear})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Dotação Atualizada"
          value={fmtCompact(summary.total_dotacao)}
          subtext="Total autorizado"
          accent
        />
        <KPICard
          title="Empenhado"
          value={fmtCompact(summary.total_empenhado)}
          subtext="Compromissado"
        />
        <KPICard
          title="Liquidado"
          value={fmtCompact(summary.total_liquidado)}
          subtext="Serviços atestados"
        />
        <KPICard
          title="Pago"
          value={fmtCompact(summary.total_pago)}
          subtext="Efetivamente desembolsado"
        />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Funil da Execução Orçamentária"
          description="Fluxo contínuo desde a aprovação da dotação até o pagamento final"
        />
        <div className="rounded-xl border border-borderLine bg-white p-6">
          <FunnelWaterfall data={funnelData} height={280} />
        </div>
      </div>

      <div>
        <SectionHeader
          title="Execução por Órgão"
          description="Quadro comparativo de cumprimento orçamentário por unidade gestora"
        />
        <DenseTable
          data={items}
          columns={orgaosCols}
          searchableKeys={["descricao", "codigo"]}
        />
      </div>
    </div>
  );
}
