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

export async function loadDespesasData(
  portalSlug: string,
  searchParams: DespesasSearchParams,
) {
  const context = parseDespesasContext(searchParams);
  const { selectedYear, entidadesIds } = context;
  const empresaIds = await resolveEmpresaIds(portalSlug, entidadesIds);

  const portalConfig = await getPortalConfig();

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
    getAnaliseDespesasMetrics(portalSlug, selectedYear, empresaIds),
    getMetricasGeraisDespesas(selectedYear, entidadesIds, portalSlug),
    getImpactoGastosLocais({
      year: selectedYear,
      empresaIds: entidadesIds,
      cidadeClean: portalConfig?.cidadeClean || "",
      portalSlug,
    }),
    getConcentracaoFornecedores(selectedYear, entidadesIds, portalSlug),
    getRestosAPagarResumo(selectedYear, entidadesIds, portalSlug),
    getDespesasPorUnidade(selectedYear, entidadesIds, portalSlug),
    getResumoDiarias(selectedYear, entidadesIds, portalSlug),
    getPrincipaisBeneficiariosDiarias({
      year: selectedYear,
      limit: 10,
      empresaIds: entidadesIds,
      portalSlug,
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
