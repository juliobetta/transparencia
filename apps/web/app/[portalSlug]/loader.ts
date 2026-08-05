import {
  getEntidades,
  getExecucaoOrcamentariaMetrics,
  getFolhaVsServicos,
  getFontesReceitaMetrics,
  getLicitacaoGaps,
  getPercentualChefiasEfetivas,
  getPortalConfig,
  getPosicaoFiscalDetalhesMetrics,
  getPosicaoFiscalMetrics,
} from "@transparencia/db";

export interface PortalRouteSearchParams {
  ano?: string;
  entidades?: string;
}

export interface PortalRouteContext {
  currentYear: number;
  selectedYear: number;
  isCurrentYear: boolean;
  entidadesIds?: string[];
}

export function parsePortalRouteContext(
  searchParams: PortalRouteSearchParams,
): PortalRouteContext {
  const currentYear = new Date().getFullYear();
  const selectedYear = searchParams.ano
    ? Number(searchParams.ano)
    : currentYear;
  const entidadesIds = searchParams.entidades
    ? searchParams.entidades.split(",").filter(Boolean)
    : undefined;

  return {
    currentYear,
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
    entidadesIds,
  };
}

function requirePortalSlug(portalSlug: string): string {
  const normalized = portalSlug.trim();
  if (!normalized) {
    throw new Error("portalSlug vazio: o tenant deve ser informado.");
  }
  return normalized;
}

async function resolveEmpresaIds(
  portalSlug: string,
  entidadesIds?: string[],
): Promise<string[]> {
  if (entidadesIds && entidadesIds.length > 0) {
    return entidadesIds;
  }

  const entidades = await getEntidades(portalSlug);
  return entidades.map((entidade) => entidade.id).filter(Boolean);
}

function requireEmpresaIdsForMetrics(
  portalSlug: string,
  empresaIds: string[],
): string[] {
  if (empresaIds.length === 0) {
    throw new Error(
      `Nenhuma entidade encontrada para o portal ${portalSlug}; chamada de métricas abortada.`,
    );
  }
  return empresaIds;
}

function summarizeExecucaoMetrics(
  metrics: Awaited<ReturnType<typeof getExecucaoOrcamentariaMetrics>>,
) {
  const totalEmpenhado = metrics.reduce(
    (acc, item) => acc + item.totalEmpenhado,
    0,
  );
  const totalLiquidado = metrics.reduce(
    (acc, item) => acc + item.totalLiquidado,
    0,
  );
  const totalPago = metrics.reduce((acc, item) => acc + item.totalPago, 0);
  const totalDotacao = metrics.reduce(
    (acc, item) => acc + item.totalDotacaoAtualizada,
    0,
  );

  return {
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    totalDotacao,
    saldoOrcamentario: totalDotacao - totalEmpenhado,
  };
}

function mapFontesMetricToLegacy(
  fontes: NonNullable<Awaited<ReturnType<typeof getFontesReceitaMetrics>>>,
) {
  const receitaPropria = fontes.receitaPropriaArrecadado;
  const transferenciasUniao = fontes.transferenciasUniaoArrecadado;
  const transferenciasEstado = fontes.transferenciasEstadoArrecadado;
  const total = fontes.totalArrecadado;

  const pctPropriaPrevisto =
    fontes.totalPrevisto > 0
      ? (fontes.receitaPropriaPrevisto / fontes.totalPrevisto) * 100
      : 0;

  const pctArrecadado =
    fontes.totalPrevisto > 0
      ? fontes.totalArrecadado / fontes.totalPrevisto
      : 0;

  return {
    ano: fontes.ano,
    receitaPropria,
    transferenciasUniao,
    transferenciasEstado,
    total,
    pctPropria: fontes.pctPropria,
    pctPropriaPrevisto,
    alertaDependencia: fontes.alertaDependencia,
    receitaPropriaPrevisto: fontes.receitaPropriaPrevisto,
    receitaPropriaArrecadado: fontes.receitaPropriaArrecadado,
    transferenciasUniaoPrevisto: fontes.transferenciasUniaoPrevisto,
    transferenciasUniaoArrecadado: fontes.transferenciasUniaoArrecadado,
    transferenciasEstadoPrevisto: fontes.transferenciasEstadoPrevisto,
    transferenciasEstadoArrecadado: fontes.transferenciasEstadoArrecadado,
    totalPrevisto: fontes.totalPrevisto,
    totalArrecadado: fontes.totalArrecadado,
    pctArrecadado,
    totalPctChange: null,
    emendasTotalArrecadado: fontes.emendasTotalArrecadado,
    emendasPixArrecadado: fontes.emendasPixArrecadado,
    emendasIndividuaisArrecadado: fontes.emendasIndividuaisArrecadado,
    fpmArrecadado: fontes.fpmArrecadado,
    icmsArrecadado: fontes.icmsArrecadado,
    issIptuArrecadado: fontes.issIptuArrecadado,
  };
}

export async function loadVisaoGeralData(
  portalSlug: string,
  searchParams: PortalRouteSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parsePortalRouteContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const empresaIds = requireEmpresaIdsForMetrics(
    tenantSlug,
    await resolveEmpresaIds(tenantSlug, entidadesIds),
  );

  const [
    portalConfig,
    posicaoMetricas,
    execMetricas,
    gaps,
    fontesMetricas,
    posicaoDetalhada,
    folhaData,
    pctChefiasEfetivas,
  ] = await Promise.all([
    getPortalConfig(tenantSlug),
    getPosicaoFiscalMetrics(tenantSlug, selectedYear, empresaIds),
    getExecucaoOrcamentariaMetrics(tenantSlug, selectedYear, empresaIds),
    getLicitacaoGaps(selectedYear, entidadesIds),
    getFontesReceitaMetrics(tenantSlug, selectedYear, empresaIds),
    getPosicaoFiscalDetalhesMetrics(tenantSlug, selectedYear, empresaIds),
    getFolhaVsServicos({
      years: [selectedYear],
      empresaIds: entidadesIds,
      portalSlug: tenantSlug,
    }),
    getPercentualChefiasEfetivas(selectedYear, entidadesIds),
  ]);

  const execSummary = summarizeExecucaoMetrics(execMetricas);
  const totalArrecadado =
    posicaoMetricas?.totalArrecadado ?? fontesMetricas?.totalArrecadado ?? 0;
  const despesasPagas = posicaoMetricas?.despesasPagas ?? execSummary.totalPago;
  const restosPagosNoAno = posicaoMetricas?.restosPagosNoAno ?? 0;

  const totalSaidasMetricas = despesasPagas + restosPagosNoAno;
  const saldoEstimado =
    posicaoMetricas?.saldoEstimado ?? totalArrecadado - totalSaidasMetricas;

  const posicao = {
    totalArrecadado,
    despesasPagas,
    restosPagosNoAno,
    totalSaidas: totalSaidasMetricas,
    saldoEstimado,
    saldoAposRestos: saldoEstimado - posicaoDetalhada.restosPendentesTotal,
    restosPendentes: posicaoDetalhada.restosPendentes,
    restosPendentesTotal: posicaoDetalhada.restosPendentesTotal,
    restosPendentesAnteriores: posicaoDetalhada.restosPendentesAnteriores,
    topCredoresAdmAtual: posicaoDetalhada.topCredoresAdmAtual,
    totalCredoresAdmAtual: posicaoDetalhada.totalCredoresAdmAtual,
  };

  return {
    portalSlug: tenantSlug,
    context,
    portalConfig,
    posicao,
    execSummary,
    gaps,
    fonte: fontesMetricas ? mapFontesMetricToLegacy(fontesMetricas) : undefined,
    folha: folhaData[0] || { percentualFolha: 0 },
    pctChefiasEfetivas,
  };
}
