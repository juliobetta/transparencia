import {
  getExecucaoOrcamentaria,
  getOrcamentoFuncional,
  summarizeExecucao,
} from "@transparencia/db";
import {
  DenseTable,
  FunnelExecucaoHorizontal,
  fmtCompact,
  GastoPorFuncaoBars,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface OrcamentoPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function OrcamentoPage({
  params,
  searchParams,
}: OrcamentoPageProps) {
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

  const items = await getExecucaoOrcamentaria(selectedYear, entidadesIds);
  const summary = summarizeExecucao(items);
  const funcionalData = await getOrcamentoFuncional(selectedYear, entidadesIds);

  const partialPeriod = getPartialYearPeriod();

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

  // Agrupamento por função de governo
  const funcMap: Record<string, number> = {};
  for (const item of funcionalData) {
    const fname = item.funcaoNome || "Outras funções";
    funcMap[fname] = (funcMap[fname] || 0) + (item.pago || item.empenhado || 0);
  }
  const funcItems = Object.entries(funcMap)
    .map(([funcao, valor]) => ({ funcao, valor }))
    .sort((a, b) => b.valor - a.valor);

  const orgaosCols = [
    { header: "Órgão / Unidade", accessorKey: "descricao" as const },
    {
      header: "Dotação (R$)",
      accessorKey: "dotacaoAtualizada" as const,
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
    <div className="space-y-6">
      {/* Eyebrow + Título + Subtítulo */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="font-bold font-serif text-3xl text-slate-900">
          Execução Orçamentária
        </h1>
        <p className="mt-2 text-sm text-subtleText leading-relaxed">
          Cada real passa por quatro estágios legais antes de sair do caixa:{" "}
          <strong className="font-semibold text-ink">reservar</strong>{" "}
          (empenho),{" "}
          <strong className="font-semibold text-ink">
            confirmar a entrega
          </strong>{" "}
          (liquidação) e{" "}
          <strong className="font-semibold text-ink">pagar</strong>. Veja quanto
          do orçamento já avançou em cada etapa.
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Dotação Atualizada"
          value={fmtCompact(totalDotacao)}
          subtext="100% autorizado"
          accent
        />
        <KPICard
          title="Empenhado"
          value={fmtCompact(totalEmpenhado)}
          subtext={`${empPct.toFixed(0)}% da dotação`}
        />
        <KPICard
          title="Liquidado"
          value={fmtCompact(totalLiquidado)}
          subtext={`${liqPct.toFixed(0)}% da dotação`}
        />
        <KPICard
          title="Pago"
          value={fmtCompact(totalPago)}
          subtext={`${pagPct.toFixed(0)}% da dotação`}
        />
      </KPIGrid>

      {/* Funil da Execução */}
      <FunnelExecucaoHorizontal stages={funnelStages} />

      {/* Para onde vai o gasto, por função */}
      {funcItems.length > 0 && (
        <div className="space-y-4 border-ink border-t-2 pt-6">
          <div className="flex items-baseline justify-between">
            <h2 className="font-bold font-serif text-ink text-xl">
              Para onde vai o gasto, por função
            </h2>
            <span className="font-medium text-subtleText text-xs">
              valor pago por função
            </span>
          </div>

          <GastoPorFuncaoBars items={funcItems} />
        </div>
      )}

      {/* Execução por Órgão */}
      <div className="space-y-4 border-ink border-t-2 pt-6">
        <h2 className="font-bold font-serif text-ink text-xl">
          Execução por Órgão e Unidade Gestora
        </h2>
        <DenseTable
          data={items}
          columns={orgaosCols}
          searchableKeys={["descricao"]}
        />
      </div>
    </div>
  );
}
