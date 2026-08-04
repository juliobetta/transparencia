import type { MetricasDespesas } from "@transparencia/db";
import {
  getAnaliseDespesasMetrics,
  getConcentracaoFornecedores,
  getDespesasPorUnidade,
  getEntidades,
  getImpactoGastosLocais,
  getMetricasGeraisDespesas,
  getPortalConfig,
  getPrincipaisBeneficiariosDiarias,
  getRestosAPagarResumo,
  getResumoDiarias,
} from "@transparencia/db";

export interface DespesasSearchParams {
  ano?: string;
  entidades?: string;
}

export interface DespesasContext {
  selectedYear: number;
  isCurrentYear: boolean;
  entidadesIds?: string[];
}

export function parseDespesasContext(
  searchParams: DespesasSearchParams,
): DespesasContext {
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

function summarizeAnaliseDespesasMetrics(
  metrics: Awaited<ReturnType<typeof getAnaliseDespesasMetrics>>,
): MetricasDespesas {
  const totais = metrics.reduce(
    (acc, item) => {
      acc.empenhado += item.totalEmpenhado;
      acc.liquidado += item.totalLiquidado;
      acc.pago += item.totalPago;
      return acc;
    },
    { empenhado: 0, liquidado: 0, pago: 0 },
  );

  return {
    empenhado: totais.empenhado,
    liquidado: totais.liquidado,
    pago: totais.pago,
    taxaLiquidacao:
      totais.empenhado > 0 ? (totais.liquidado / totais.empenhado) * 100 : 0,
    taxaPagamento:
      totais.empenhado > 0 ? (totais.pago / totais.empenhado) * 100 : 0,
  };
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

export async function loadDespesasData(
  portalSlug: string,
  searchParams: DespesasSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parseDespesasContext(searchParams);
  const { selectedYear, entidadesIds } = context;
  const empresaIds = requireEmpresaIdsForMetrics(
    tenantSlug,
    await resolveEmpresaIds(tenantSlug, entidadesIds),
  );

  const portalConfig = await getPortalConfig(tenantSlug);

  const [
    analiseDespesasMetrics,
    metricasGerais,
    impactoLocais,
    concentracao,
    restosResumo,
    despesasUnidades,
    diariasResumo,
    diariasBeneficiarios,
  ] = await Promise.all([
    getAnaliseDespesasMetrics(tenantSlug, selectedYear, empresaIds),
    getMetricasGeraisDespesas(selectedYear, empresaIds, tenantSlug),
    getImpactoGastosLocais({
      year: selectedYear,
      empresaIds,
      cidadeClean: portalConfig?.cidadeClean || "",
      portalSlug: tenantSlug,
    }),
    getConcentracaoFornecedores(selectedYear, empresaIds, tenantSlug),
    getRestosAPagarResumo(selectedYear, empresaIds, tenantSlug),
    getDespesasPorUnidade(selectedYear, empresaIds, tenantSlug),
    getResumoDiarias(selectedYear, empresaIds, tenantSlug),
    getPrincipaisBeneficiariosDiarias({
      year: selectedYear,
      limit: 10,
      empresaIds,
      portalSlug: tenantSlug,
    }),
  ]);

  // Fallback legado controlado: mantém paridade enquanto alguns blocos de Despesas
  // (HHI, diárias, restos e concentração detalhada) ainda dependem de readers não métricos.
  const metricasGeraisCompostas =
    analiseDespesasMetrics.length > 0
      ? summarizeAnaliseDespesasMetrics(analiseDespesasMetrics)
      : metricasGerais;

  return {
    context,
    metricasGerais: metricasGeraisCompostas,
    impactoLocais,
    concentracao,
    restosResumo,
    despesasUnidades,
    diariasResumo,
    diariasBeneficiarios,
  };
}
