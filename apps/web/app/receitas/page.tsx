import { getFontesReceita } from "@transparencia/db";
import {
  AlertBox,
  BarChartH,
  DenseTable,
  fmtCompact,
  fmtPercent,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

export default async function ReceitasPage() {
  const currentYear = 2025;
  const fontes = await getFontesReceita([currentYear]);
  const rec = fontes[0] || {
    receita_propria: 0,
    transferencias_uniao: 0,
    transferencias_estado: 0,
    total: 0,
    pct_propria: 0,
    alerta_dependencia: false,
    receita_propria_previsto: 0,
    receita_propria_arrecadado: 0,
    transferencias_uniao_previsto: 0,
    transferencias_uniao_arrecadado: 0,
    transferencias_estado_previsto: 0,
    transferencias_estado_arrecadado: 0,
    total_previsto: 0,
    total_arrecadado: 0,
  };

  const chartData = [
    {
      label: "Transferências da União (Federal)",
      value: rec.transferencias_uniao_arrecadado,
    },
    {
      label: "Transferências do Estado (Estadual)",
      value: rec.transferencias_estado_arrecadado,
    },
    {
      label: "Receita Própria (Municipal)",
      value: rec.receita_propria_arrecadado,
    },
  ];

  const tableData = [
    {
      fonte: "Receita Própria (Municipal)",
      previsto: rec.receita_propria_previsto,
      arrecadado: rec.receita_propria_arrecadado,
      pct:
        rec.receita_propria_previsto > 0
          ? (rec.receita_propria_arrecadado / rec.receita_propria_previsto) *
            100
          : 0,
    },
    {
      fonte: "Transferências da União",
      previsto: rec.transferencias_uniao_previsto,
      arrecadado: rec.transferencias_uniao_arrecadado,
      pct:
        rec.transferencias_uniao_previsto > 0
          ? (rec.transferencias_uniao_arrecadado /
              rec.transferencias_uniao_previsto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferencias_estado_previsto,
      arrecadado: rec.transferencias_estado_arrecadado,
      pct:
        rec.transferencias_estado_previsto > 0
          ? (rec.transferencias_estado_arrecadado /
              rec.transferencias_estado_previsto) *
            100
          : 0,
    },
  ];

  const tableCols = [
    { header: "Origem da Receita", accessorKey: "fonte" as const },
    {
      header: "Previsto (R$)",
      accessorKey: "previsto" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Arrecadado (R$)",
      accessorKey: "arrecadado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Execução (%)",
      accessorKey: "pct" as const,
      align: "right" as const,
      format: "percent" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Fontes de Receita
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Composição da arrecadação municipal e nível de dependência de
          transferências externas
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Total Arrecadado"
          value={fmtCompact(rec.total_arrecadado)}
          subtext={`Previsto: ${fmtCompact(rec.total_previsto)}`}
          accent
        />
        <KPICard
          title="Receita Própria"
          value={fmtCompact(rec.receita_propria_arrecadado)}
          subtext={`Participação: ${fmtPercent(rec.pct_propria)}`}
        />
        <KPICard
          title="Transferências União"
          value={fmtCompact(rec.transferencias_uniao_arrecadado)}
          subtext="Recursos Federais"
        />
        <KPICard
          title="Transferências Estado"
          value={fmtCompact(rec.transferencias_estado_arrecadado)}
          subtext="Recursos Estaduais"
        />
      </KPIGrid>

      {rec.alerta_dependencia && (
        <AlertBox
          type="danger"
          title="Alerta: Alta Dependência de Transferências Externa"
        >
          A receita própria representa menos de 10% do total arrecadado (
          {fmtPercent(rec.pct_propria)}). O município apresenta elevada
          vulnerabilidade fiscal a repasses federais e estaduais.
        </AlertBox>
      )}

      <div>
        <SectionHeader
          title="Distribuição das Fontes de Receita"
          description="Comparativo visual do volume de recursos por origem"
        />
        <div className="rounded-xl border border-borderLine bg-white p-6">
          <BarChartH data={chartData} />
        </div>
      </div>

      <div>
        <SectionHeader
          title="Detalhamento Orçamentário de Receitas"
          description="Valores previstos vs efetivamente arrecadados por categoria"
        />
        <DenseTable data={tableData} columns={tableCols} />
      </div>
    </div>
  );
}
