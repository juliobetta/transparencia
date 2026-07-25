import { getMetricasGeraisDespesas, getDespesasPorUnidade, getComposicaoDespesa, getTransacoesPesquisaveis } from "@transparencia/db";
import { KPICard, KPIGrid, SectionHeader, DenseTable, BarChartH, fmtCompact, fmtCurrency, fmtPercent } from "@transparencia/ui";

export const revalidate = 60;

export default async function DespesasPage() {
  const currentYear = 2025;
  const metricas = await getMetricasGeraisDespesas(currentYear);
  const unidades = await getDespesasPorUnidade(currentYear);
  const composicao = await getComposicaoDespesa(currentYear);
  const transacoes = await getTransacoesPesquisaveis(currentYear, "", 50);

  const chartData = composicao.map((c) => ({
    label: c.categoria,
    value: c.pago,
  }));

  const transacoesCols = [
    { header: "Data", accessorKey: "data" as const },
    { header: "Unidade / Órgão", accessorKey: "unidade" as const },
    { header: "Fornecedor / Credor", accessorKey: "fornecedor" as const },
    { header: "Histórico", accessorKey: "descricao" as const },
    {
      header: "Valor Pago",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold font-serif text-ink">Análise de Despesas</h1>
        <p className="text-sm text-subtleText mt-1">
          Detalhamento de gastos públicos, liquidações e pagamentos ({currentYear})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard title="Total Empenhado" value={fmtCompact(metricas.empenhado)} subtext="Compromissos assumidos" accent />
        <KPICard title="Total Liquidado" value={fmtCompact(metricas.liquidado)} subtext={`Taxa: ${fmtPercent(metricas.taxa_liquidacao)}`} />
        <KPICard title="Total Pago" value={fmtCompact(metricas.pago)} subtext={`Taxa: ${fmtPercent(metricas.taxa_pagamento)}`} />
        <KPICard title="Saldo Pendente" value={fmtCompact(metricas.empenhado - metricas.pago)} subtext="A liquidar / pagar" />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Composição da Despesa por Categoria"
          description="Gastos por natureza de despesa (Portaria 163/2001)"
        />
        <div className="bg-white border border-borderLine rounded-xl p-6">
          <BarChartH data={chartData} />
        </div>
      </div>

      <div>
        <SectionHeader
          title="Transações e Empenhos Recentes"
          description="Pesquisa direta em empenhos e liquidações efetuadas"
        />
        <DenseTable data={transacoes} columns={transacoesCols} searchableKeys={["fornecedor", "descricao", "unidade"]} />
      </div>
    </div>
  );
}
