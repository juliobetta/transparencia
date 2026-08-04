import { fmtCompact, getPartialYearPeriod } from "@transparencia/ui";
import type { loadOrcamentoData } from "./loader";

type OrcamentoRawData = Awaited<ReturnType<typeof loadOrcamentoData>>;

export function buildOrcamentoViewModel(raw: OrcamentoRawData) {
  const { summary, funcionalData } = raw;

  const totalDotacao = summary.totalDotacao;
  const totalEmpenhado = summary.totalEmpenhado;
  const totalLiquidado = summary.totalLiquidado;
  const totalPago = summary.totalPago;

  const empPct = totalDotacao > 0 ? (totalEmpenhado / totalDotacao) * 100 : 0;
  const liqPct = totalDotacao > 0 ? (totalLiquidado / totalDotacao) * 100 : 0;
  const pagPct = totalDotacao > 0 ? (totalPago / totalDotacao) * 100 : 0;

  const funnelStages = [
    {
      name: "Dotação",
      value: totalDotacao,
      formattedValue: fmtCompact(totalDotacao),
      colorClass: "bg-blue-600",
    },
    {
      name: "Empenhado",
      value: totalEmpenhado,
      formattedValue: fmtCompact(totalEmpenhado),
      colorClass: "bg-blue-500",
    },
    {
      name: "Liquidado",
      value: totalLiquidado,
      formattedValue: fmtCompact(totalLiquidado),
      colorClass: "bg-sky-500",
    },
    {
      name: "Pago",
      value: totalPago,
      formattedValue: fmtCompact(totalPago),
      colorClass: "bg-cyan-500",
    },
  ];

  const funcMap: Record<string, number> = {};
  for (const item of funcionalData) {
    const fname = item.funcaoNome || "Outras funções";
    funcMap[fname] = (funcMap[fname] || 0) + (item.pago || item.empenhado || 0);
  }

  const funcItems = Object.entries(funcMap)
    .map(([funcao, valor]) => ({ funcao, valor }))
    .sort((a, b) => b.valor - a.valor);

  const orgaosCols = [
    {
      header: "Órgão / Unidade",
      accessorKey: "descricao" as const,
    },
    {
      header: "Dotação",
      accessorKey: "dotacaoAtualizada" as const,
      align: "right" as const,
      format: "currency" as const,
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
    {
      header: "Execução",
      accessorKey: "alerta" as const,
      align: "center" as const,
      format: "statusBadge" as const,
    },
  ];

  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    partialPeriod: getPartialYearPeriod(),
    items: raw.items,
    totalDotacao,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    empPct,
    liqPct,
    pagPct,
    funnelStages,
    funcItems,
    orgaosCols,
  };
}
