import {
  getComposicaoDespesa,
  getDespesasPorUnidade,
  getMetricasGeraisDespesas,
  getTransacoesPesquisaveis,
} from "@transparencia/db";
import {
  BarChartH,
  DenseTable,
  fmtCompact,
  fmtPercent,
  KPICard,
  KPIGrid,
  SectionHeader,
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
  const { portalSlug: _portalSlug } = await params;
  const resolvedSearchParams = await searchParams;

  const currentYear = new Date().getFullYear();
  const selectedYear = resolvedSearchParams.ano
    ? Number(resolvedSearchParams.ano)
    : currentYear;
  const entidadesIds = resolvedSearchParams.entidades
    ? resolvedSearchParams.entidades.split(",").filter(Boolean)
    : undefined;

  const isCurrentYear = selectedYear === currentYear;

  const metricas = await getMetricasGeraisDespesas(selectedYear, entidadesIds);
  const _unidades = await getDespesasPorUnidade(selectedYear, entidadesIds);
  const composicao = await getComposicaoDespesa(selectedYear, entidadesIds);
  const transacoes = await getTransacoesPesquisaveis(
    selectedYear,
    "",
    50,
    entidadesIds,
  );

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
        <h1 className="font-bold font-serif text-3xl text-ink">
          Análise de Despesas
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Detalhamento de gastos públicos, liquidações e pagamentos (
          {selectedYear}
          {isCurrentYear ? " · parcial" : ""})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Total Empenhado"
          value={fmtCompact(metricas.empenhado)}
          subtext="Compromissos assumidos"
          accent
        />
        <KPICard
          title="Total Liquidado"
          value={fmtCompact(metricas.liquidado)}
          subtext={`Taxa: ${fmtPercent(metricas.taxa_liquidacao)}`}
        />
        <KPICard
          title="Total Pago"
          value={fmtCompact(metricas.pago)}
          subtext={`Taxa: ${fmtPercent(metricas.taxa_pagamento)}`}
        />
        <KPICard
          title="Saldo Pendente"
          value={fmtCompact(metricas.empenhado - metricas.pago)}
          subtext="A liquidar / pagar"
        />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Composição da Despesa por Categoria"
          description="Gastos por natureza de despesa (Portaria 163/2001)"
        />
        <div className="rounded-xl border border-borderLine bg-white p-6">
          <BarChartH data={chartData} />
        </div>
      </div>

      <div>
        <SectionHeader
          title="Transações e Empenhos Recentes"
          description="Pesquisa direta em empenhos e liquidações efetuadas"
        />
        <DenseTable
          data={transacoes}
          columns={transacoesCols}
          searchableKeys={["fornecedor", "descricao", "unidade"]}
        />
      </div>
    </div>
  );
}
