import {
  getExecucaoOrcamentaria,
  getFolhaVsServicos,
  getFontesReceita,
  getLicitacaoGaps,
  getPercentualChefiasEfetivas,
  getPortalConfig,
  getPosicaoFiscal,
  summarizeExecucao,
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

export async function loadVisaoGeralData(
  portalSlug: string,
  searchParams: PortalRouteSearchParams,
) {
  const context = parsePortalRouteContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const [
    portalConfig,
    posicao,
    execItems,
    gaps,
    fontes,
    folhaData,
    pctChefiasEfetivas,
  ] = await Promise.all([
    getPortalConfig(),
    getPosicaoFiscal(selectedYear, entidadesIds, portalSlug),
    getExecucaoOrcamentaria(selectedYear, entidadesIds),
    getLicitacaoGaps(selectedYear, entidadesIds),
    getFontesReceita([selectedYear], entidadesIds),
    getFolhaVsServicos({
      years: [selectedYear],
      empresaIds: entidadesIds,
      portalSlug,
    }),
    getPercentualChefiasEfetivas(selectedYear, entidadesIds),
  ]);

  return {
    portalSlug,
    context,
    portalConfig,
    posicao,
    execItems,
    execSummary: summarizeExecucao(execItems),
    gaps,
    fonte: fontes[0],
    folha: folhaData[0] || { percentualFolha: 0 },
    pctChefiasEfetivas,
  };
}
