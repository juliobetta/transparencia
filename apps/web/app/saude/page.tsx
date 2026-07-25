import { getHistoriaSaude } from "@transparencia/db";
import { KPICard, KPIGrid, SectionHeader, AlertBox, DenseTable, fmtCompact, fmtCurrency, fmtPercent } from "@transparencia/ui";

export const dynamic = "force-dynamic";

export default async function SaudePage() {
  const currentYear = 2025;
  const saude = await getHistoriaSaude(currentYear);

  const emendasCols = [
    { header: "Nº", accessorKey: "Nº" as const },
    { header: "Autor da Emenda", accessorKey: "Autor" as const },
    { header: "Objeto", accessorKey: "Objeto" as const },
    {
      header: "Valor Autorizado",
      accessorKey: "Valor Autorizado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Empenhado",
      accessorKey: "Empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold font-serif text-ink">Painel da Saúde</h1>
        <p className="text-sm text-subtleText mt-1">
          Execução orçamentária do Fundo Municipal de Saúde, emendas parlamentares e medicamentos ({currentYear})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard title="Dotação da Saúde" value={fmtCompact(saude.orcamento.dotacao)} subtext="Orçamento aprovado" accent />
        <KPICard title="Empenhado" value={fmtCompact(saude.orcamento.empenhado)} subtext={`Execução: ${fmtPercent(saude.orcamento.taxa_execucao * 100)}`} />
        <KPICard title="Emendas Parlamentares" value={fmtCompact(saude.emendas_total)} subtext={`${saude.emendas.length} emendas destinadas`} />
        <KPICard title="Status Orçamentário" value={saude.orcamento.alerta_sub_execucao ? "Subexecutado" : "Normal"} alert={saude.orcamento.alerta_sub_execucao} />
      </KPIGrid>

      {saude.orcamento.alerta_sub_execucao && (
        <AlertBox type="warning" title="Alerta de Subexecução Orçamentária">
          A execução da Saúde está abaixo de 70% da dotação aprovada para o exercício.
        </AlertBox>
      )}

      <div>
        <SectionHeader
          title="Emendas Parlamentares Destinadas à Saúde"
          description="Relação de recursos parlamentares recebidos pelo Fundo Municipal de Saúde"
        />
        <DenseTable data={saude.emendas} columns={emendasCols} searchableKeys={["Autor", "Objeto", "Nº"]} />
      </div>
    </div>
  );
}
