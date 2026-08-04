import {
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  toTitleCase,
} from "@transparencia/ui";
import type { loadVisaoGeralData } from "./loader";

type VisaoGeralRawData = Awaited<ReturnType<typeof loadVisaoGeralData>>;

export function buildVisaoGeralViewModel(raw: VisaoGeralRawData) {
  const {
    portalSlug,
    context,
    portalConfig,
    posicao,
    execSummary,
    gaps,
    fonte,
  } = raw;

  const selectedYear = context.selectedYear;
  const isCurrentYear = context.isCurrentYear;
  const portalName = portalConfig?.displayName;

  const folhaPct = Number((raw.folha.percentualFolha || 0).toFixed(1));

  const totalArr = posicao.totalArrecadado || fonte?.totalArrecadado || 0;
  const uniaoArr = fonte?.transferenciasUniaoArrecadado || 0;
  const estadoArr = fonte?.transferenciasEstadoArrecadado || 0;
  const propriaArr =
    fonte?.receitaPropriaArrecadado ||
    Math.max(0, totalArr - uniaoArr - estadoArr);

  const uniaoPct = totalArr > 0 ? Math.round((uniaoArr / totalArr) * 100) : 0;
  const estadoPct = totalArr > 0 ? Math.round((estadoArr / totalArr) * 100) : 0;
  const propriaPct = totalArr > 0 ? Math.max(0, 100 - uniaoPct - estadoPct) : 0;

  const realizationPct =
    execSummary.totalDotacao > 0
      ? Math.round((totalArr / execSummary.totalDotacao) * 100)
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

  const totalDotacao = execSummary.totalDotacao;
  const totalEmpenhado = execSummary.totalEmpenhado;
  const totalLiquidado = execSummary.totalLiquidado;
  const totalPago = execSummary.totalPago;

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

  const acimaLimiteCount = gaps.filter((g) => g.acimaLimite).length;
  const saudeGapsCount = gaps.filter((g) => g.orgaoSaude).length;

  const maxPendente = Math.max(
    ...posicao.restosPendentes.map((r) => r.pendente),
    1,
  );

  const despesasCardData = {
    title: "Despesas",
    linkText: "Restos a pagar →",
    linkHref: `/${portalSlug}/despesas`,
    totalRestosPagarFormatted: fmtCompact(posicao.restosPendentesTotal),
    subtext: `pendentes a ${posicao.totalCredoresAdmAtual || 0} fornecedores`,
    antiguidadeBars: posicao.restosPendentes.map((r) => ({
      year: String(r.ano),
      amountFormatted: fmtCompact(r.pendente),
      percentage: Math.round((r.pendente / maxPendente) * 100),
    })),
    footerText:
      posicao.restosPendentesAnteriores > 0
        ? `Passivo anterior: ${fmtCompact(posicao.restosPendentesAnteriores)}`
        : "Sem pendências de anos anteriores",
  };

  const licitacoesCardData = {
    title: "Licitações",
    linkText: "Contratos →",
    linkHref: `/${portalSlug}/licitacoes`,
    items: [
      {
        count: acimaLimiteCount,
        label: "Acima do limite s/ licitação",
        isAlert: acimaLimiteCount > 0,
      },
      {
        count: gaps.length,
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
    linkHref: `/${portalSlug}/pessoal`,
    receitaFolhaPercentFormatted: fmtPercent(folhaPct),
    receitaFolhaPercentValue: folhaPct,
    subtext: "da receita comprometida com a folha",
    lrfLimitPercentValue: 54,
    lrfLimitPercentFormatted: "54% LRF",
    footerText:
      raw.pctChefiasEfetivas !== null
        ? `${raw.pctChefiasEfetivas}% das chefias com servidores efetivos`
        : "Sem dados de ocupação de chefias no período",
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

  const sanitizedCredores = posicao.topCredoresAdmAtual.map((credor) => ({
    ...credor,
    Fornecedor: toTitleCase(credor.Fornecedor),
  }));

  const partialPeriod = getPartialYearPeriod();
  const periodText = `VISÃO GERAL · EXERCÍCIO ${selectedYear}${
    isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""
  }`;
  const arrecadadoTitle = isCurrentYear
    ? "Arrecadado no ano até agora"
    : "Arrecadado no exercício";

  const heroHeadline = (
    <>
      De cada R$ 100 que entram no caixa,{" "}
      <span className="text-[oklch(0.55_0.11_250)]">R$ {propriaPct}</span> a
      cidade arrecada sozinha.
    </>
  );

  const heroSummary = isCurrentYear ? (
    <p>
      O município já recebeu <b>{fmtCompact(totalArr)}</b> em {selectedYear} —{" "}
      <b>{realizationPct}%</b> do previsto para o ano. Quase todo esse dinheiro
      vem de repasses da União e do Estado, o que torna as contas sensíveis a
      decisões tomadas longe daqui.
    </p>
  ) : (
    <p>
      O município arrecadou <b>{fmtCompact(totalArr)}</b> em {selectedYear} —{" "}
      <b>{realizationPct}%</b> do previsto para o exercício. Quase todo esse
      dinheiro veio de repasses da União e do Estado, o que torna as contas
      sensíveis a decisões tomadas longe daqui.
    </p>
  );

  return {
    portalName,
    periodText,
    arrecadadoTitle,
    heroHeadline,
    heroSummary,
    selectedYear,
    realizationPercent: realizationPct,
    totalArrecadado: posicao.totalArrecadado,
    previstoTotal: execSummary.totalDotacao,
    originBreakdown,
    pipelineStages,
    despesasCardData,
    licitacoesCardData,
    pessoalCardData,
    sanitizedCredores,
    credoresCols,
    orcamentoDetailUrl: `/${portalSlug}/orcamento`,
  };
}
