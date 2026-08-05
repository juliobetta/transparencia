import {
  getEntidades,
  getExecucaoOrcamentariaMetrics,
  getOrcamentoFuncionalMetrics,
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

function mapExecucaoMetricsToLegacyItems(
  metrics: Awaited<ReturnType<typeof getExecucaoOrcamentariaMetrics>>,
) {
  return metrics
    .map((item) => ({
      ano: item.ano,
      empresa: item.unidadeCodigo || item.orgaoCodigo,
      codigo: item.orgaoCodigo,
      descricao:
        item.orgaoNome ||
        `Órgão ${item.orgaoCodigo} · Unidade ${item.unidadeCodigo}`,
      empenhado: item.totalEmpenhado,
      liquidado: item.totalLiquidado,
      pago: item.totalPago,
      dotacaoAtualizada: item.totalDotacaoAtualizada,
      taxaExecucao: item.taxaExecucao,
      alerta: item.alertaExecucao,
    }))
    .sort((a, b) => {
      // sort by dotacaoAtualizada descending, then by descricao ascending
      if (b.dotacaoAtualizada !== a.dotacaoAtualizada) {
        return b.dotacaoAtualizada - a.dotacaoAtualizada;
      }
      return a.descricao.localeCompare(b.descricao);
    });
}

export async function loadOrcamentoData(
  portalSlug: string,
  searchParams: OrcamentoSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parseOrcamentoContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const empresaIds = requireEmpresaIdsForMetrics(
    tenantSlug,
    await resolveEmpresaIds(tenantSlug, entidadesIds),
  );

  const [execucaoMetrics, funcionalData] = await Promise.all([
    getExecucaoOrcamentariaMetrics(tenantSlug, selectedYear, empresaIds),
    getOrcamentoFuncionalMetrics(tenantSlug, selectedYear, empresaIds),
  ]);

  const items = mapExecucaoMetricsToLegacyItems(execucaoMetrics);

  return {
    portalSlug: tenantSlug,
    context,
    items,
    funcionalData,
    summary: summarizeExecucao(items),
  };
}
