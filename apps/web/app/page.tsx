import {
  getExecucaoOrcamentaria,
  getFontesReceita,
  getLicitacaoGaps,
  getPosicaoFiscal,
  summarizeExecucao,
} from "@transparencia/db";
import {
  AlertBox,
  CardsSecundariosVisaoGeral,
  DenseTable,
  fmtCompact,
  fmtCurrency,
  fmtPercent,
  HeroFiscalCard,
  PipelineExecucao,
  toTitleCase,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface VisaoGeralPageProps {
  cityName?: string;
}

export default async function VisaoGeralPage({
  cityName = "Porciúncula",
}: VisaoGeralPageProps) {
  const currentYear = 2025;
  const posicao = await getPosicaoFiscal(currentYear);
  const execItems = await getExecucaoOrcamentaria(currentYear);
  const execSummary = summarizeExecucao(execItems);
  const _gaps = await getLicitacaoGaps(currentYear);
  const fontes = await getFontesReceita([currentYear]);
  const fonte = fontes[0];

  const totalArr = posicao.total_arrecadado || fonte?.total_arrecadado || 0;
  const uniaoArr = fonte?.transferencias_uniao_arrecadado || 0;
  const estadoArr = fonte?.transferencias_estado_arrecadado || 0;
  const propriaArr =
    fonte?.receita_propria_arrecadado ||
    Math.max(0, totalArr - uniaoArr - estadoArr);

  const uniaoPct = totalArr > 0 ? Math.round((uniaoArr / totalArr) * 100) : 0;
  const estadoPct = totalArr > 0 ? Math.round((estadoArr / totalArr) * 100) : 0;
  const propriaPct = totalArr > 0 ? Math.max(0, 100 - uniaoPct - estadoPct) : 0;

  const realizationPct =
    execSummary.total_dotacao > 0
      ? Math.round((totalArr / execSummary.total_dotacao) * 100)
      : 0;

  const originBreakdown = [
    {
      label: "Transferências da União",
      amountPerReal: `R$ ${(uniaoArr / (totalArr || 1)).toFixed(2).replace(".", ",")}`,
      percentage: uniaoPct,
      colorClass: "bg-blue-600",
    },
    {
      label: "Transferências do Estado",
      amountPerReal: `R$ ${(estadoArr / (totalArr || 1)).toFixed(2).replace(".", ",")}`,
      percentage: estadoPct,
      colorClass: "bg-sky-500",
    },
    {
      label: "Receita Própria",
      amountPerReal: `R$ ${(propriaArr / (totalArr || 1)).toFixed(2).replace(".", ",")}`,
      percentage: propriaPct,
      colorClass: "bg-emerald-600",
    },
  ];

  const totalDotacao = execSummary.total_dotacao;
  const totalEmpenhado = execSummary.total_empenhado;
  const totalLiquidado = execSummary.total_liquidado;
  const totalPago = execSummary.total_pago;

  const empPct = totalDotacao > 0 ? (totalEmpenhado / totalDotacao) * 100 : 0;
  const liqPct = totalDotacao > 0 ? (totalLiquidado / totalDotacao) * 100 : 0;
  const pagPct = totalDotacao > 0 ? (totalPago / totalDotacao) * 100 : 0;

  const pipelineStages = [
    {
      name: "Dotação",
      formattedValue: fmtCompact(totalDotacao),
      percentage: 100,
      label: "100% autorizado",
      color: "bg-blue-600",
    },
    {
      name: "Empenhado",
      formattedValue: fmtCompact(totalEmpenhado),
      percentage: Number(empPct.toFixed(1)),
      label: `${fmtPercent(empPct)} da dotação`,
      color: "bg-indigo-600",
    },
    {
      name: "Liquidado",
      formattedValue: fmtCompact(totalLiquidado),
      percentage: Number(liqPct.toFixed(1)),
      label: `${fmtPercent(liqPct)} da dotação`,
      color: "bg-sky-600",
    },
    {
      name: "Pago",
      formattedValue: fmtCompact(totalPago),
      percentage: Number(pagPct.toFixed(1)),
      label: `${fmtPercent(pagPct)} da dotação`,
      color: "bg-emerald-600",
    },
  ];

  const acimaLimiteCount = _gaps.filter((g) => g.acima_limite).length;
  const saudeGapsCount = _gaps.filter((g) => g.orgao_saude).length;

  const maxPendente = Math.max(
    ...posicao.restos_pendentes.map((r) => r.pendente),
    1,
  );

  const despesasCardData = {
    title: "Despesas",
    linkText: "Restos a pagar →",
    linkHref: "/despesas",
    totalRestosPagarFormatted: fmtCompact(posicao.restos_pendentes_total),
    subtext: `pendentes a ${posicao.top_credores_adm_atual.length || 0} fornecedores`,
    antiguidadeBars: posicao.restos_pendentes.map((r) => ({
      year: String(r.ano),
      amountFormatted: fmtCompact(r.pendente),
      percentage: Math.round((r.pendente / maxPendente) * 100),
    })),
    footerText:
      posicao.restos_pendentes_anteriores > 0
        ? `Passivo anterior: ${fmtCompact(posicao.restos_pendentes_anteriores)}`
        : "Sem pendências de anos anteriores",
  };

  const licitacoesCardData = {
    title: "Licitações",
    linkText: "Contratos →",
    linkHref: "/licitacoes",
    items: [
      {
        count: acimaLimiteCount,
        label: "Acima do limite s/ licitação",
        isAlert: acimaLimiteCount > 0,
      },
      {
        count: _gaps.length,
        label: "Contratos sem licitação registrados",
      },
      {
        count: saudeGapsCount,
        label: "Contratos no órgão de Saúde",
      },
    ],
  };

  const pessoalCardData = {
    title: "Pessoal",
    linkText: "Folha →",
    linkHref: "/pessoal",
    receitaFolhaPercentFormatted: "48,2%",
    receitaFolhaPercentValue: 48.2,
    subtext: "da receita comprometida com a folha",
    lrfLimitPercentValue: 54,
    lrfLimitPercentFormatted: "54% LRF",
    footerText: "61% das chefias com servidores efetivos",
  };

  const credoresCols = [
    { header: "Fornecedor", accessorKey: "Fornecedor" as const },
    {
      header: "Pendente",
      accessorKey: "Pendente" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  const sanitizedCredores = posicao.top_credores_adm_atual.map((credor) => ({
    ...credor,
    Fornecedor: toTitleCase(credor.Fornecedor),
  }));

  return (
    <div className="mx-auto max-w-[1000px] space-y-9 px-10 py-8">
      {/* 1. Hero Fiscal Card */}
      <HeroFiscalCard
        cityName={cityName}
        periodText={`Visão geral · Exercício ${currentYear} (parcial)`}
        totalArrecadado={posicao.total_arrecadado}
        previstoTotal={execSummary.total_dotacao}
        realizationPercent={realizationPct}
        originBreakdown={originBreakdown}
      />

      {/* 2. Pipeline de Execução */}
      <PipelineExecucao stages={pipelineStages} />

      {/* 3. Cards Secundários */}
      <CardsSecundariosVisaoGeral
        despesas={despesasCardData}
        licitacoes={licitacoesCardData}
        pessoal={pessoalCardData}
      />

      {/* Alerta de Restos a Pagar se houver pendência anterior */}
      {posicao.restos_pendentes_anteriores > 0 && (
        <AlertBox type="warning" title="Atenção: Passivo de Gestões Anteriores">
          O município possui{" "}
          <b>{fmtCurrency(posicao.restos_pendentes_anteriores)}</b> em restos a
          pagar pendentes referentes a exercícios anteriores a {currentYear}.
        </AlertBox>
      )}

      {/* 4. Tabela Densa de Credores */}
      {sanitizedCredores.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-baseline justify-between border-[#1a1d21] border-t-2 pt-3">
            <h3 className="font-bold font-serif text-ink text-xl">
              Maiores Credores da Gestão Atual
            </h3>
            <span className="font-medium text-subtleText text-xs">
              Restos a pagar acumulados a partir de {currentYear}
            </span>
          </div>
          <DenseTable data={sanitizedCredores} columns={credoresCols} />
        </div>
      )}
    </div>
  );
}
