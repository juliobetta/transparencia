import {
  getEntidades,
  getExecucaoOrcamentariaMetrics,
  getOrcamentoFuncional,
  summarizeExecucao,
} from "@transparencia/db";

export interface OrcamentoSearchParams {
  ano?: string;
  entidades?: string;
}

export interface OrcamentoContext {
  selectedYear: number;
  isCurrentYear: boolean;
  entidadesIds?: string[];
}

export function parseOrcamentoContext(
  searchParams: OrcamentoSearchParams,
): OrcamentoContext {
  const currentYear = new Date().getFullYear();
  const selectedYear = searchParams.ano
    ? Number(searchParams.ano)
    : currentYear;
  const entidadesIds = searchParams.entidades
    ? searchParams.entidades.split(",").filter(Boolean)
    : undefined;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
    entidadesIds,
  };
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

function mapExecucaoMetricsToLegacyItems(
  metrics: Awaited<ReturnType<typeof getExecucaoOrcamentariaMetrics>>,
) {
  return metrics.map((item) => ({
    ano: item.ano,
    empresa: item.unidadeCodigo || item.orgaoCodigo,
    codigo: item.orgaoCodigo,
    descricao: `Órgão ${item.orgaoCodigo} · Unidade ${item.unidadeCodigo}`,
    empenhado: item.totalEmpenhado,
    liquidado: item.totalLiquidado,
    pago: item.totalPago,
    dotacaoAtualizada: item.totalDotacaoAtualizada,
    taxaExecucao: item.taxaExecucao,
    alerta: item.alertaExecucao,
  }));
}

export async function loadOrcamentoData(
  portalSlug: string,
  searchParams: OrcamentoSearchParams,
) {
  const context = parseOrcamentoContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const empresaIds = await resolveEmpresaIds(portalSlug, entidadesIds);

  const [execucaoMetrics, funcionalData] = await Promise.all([
    getExecucaoOrcamentariaMetrics(portalSlug, selectedYear, empresaIds),
    getOrcamentoFuncional(selectedYear, entidadesIds),
  ]);

  const items = mapExecucaoMetricsToLegacyItems(execucaoMetrics);

  return {
    portalSlug,
    context,
    items,
    funcionalData,
    summary: summarizeExecucao(items),
  };
}
