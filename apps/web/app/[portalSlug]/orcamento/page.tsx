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

  const partialPeriod = getPartialYearPeriod(new Date());

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
    { header: "Código", accessorKey: "codigo" as const },
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
        <h1 className="mt-1 font-bold font-serif text-3xl text-ink lg:text-4xl">
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

      {/* Grid dos 4 KPI Cards dos Estágios Orçamentários */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Dotação Atualizada */}
        <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
          <div className="text-subtleText text-xs">Dotação Atualizada</div>
          <div className="mt-2 font-bold font-serif text-2xl text-ink tracking-tight lg:text-3xl">
            {fmtCompact(totalDotacao)}
          </div>
          <div className="mt-2 font-medium text-subtleText text-xs">
            100% autorizado
          </div>
        </div>

        {/* Card 2: Empenhado */}
        <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
          <div className="text-subtleText text-xs">Empenhado</div>
          <div className="mt-2 font-bold font-serif text-2xl text-[#2563eb] tracking-tight lg:text-3xl">
            {fmtCompact(totalEmpenhado)}
          </div>
          <div className="mt-2 font-medium text-subtleText text-xs">
            {empPct.toFixed(0)}% da dotação
          </div>
        </div>

        {/* Card 3: Liquidado */}
        <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
          <div className="text-subtleText text-xs">Liquidado</div>
          <div className="mt-2 font-bold font-serif text-2xl text-[#0284c7] tracking-tight lg:text-3xl">
            {fmtCompact(totalLiquidado)}
          </div>
          <div className="mt-2 font-medium text-subtleText text-xs">
            {liqPct.toFixed(0)}% da dotação
          </div>
        </div>

        {/* Card 4: Pago */}
        <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
          <div className="text-subtleText text-xs">Pago</div>
          <div className="mt-2 font-bold font-serif text-2xl text-[#0891b2] tracking-tight lg:text-3xl">
            {fmtCompact(totalPago)}
          </div>
          <div className="mt-2 font-medium text-subtleText text-xs">
            {pagPct.toFixed(0)}% da dotação
          </div>
        </div>
      </div>

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
          searchableKeys={["descricao", "codigo"]}
        />
      </div>
    </div>
  );
}
