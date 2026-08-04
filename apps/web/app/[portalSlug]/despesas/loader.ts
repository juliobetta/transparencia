import {
  getConcentracaoFornecedores,
  getDespesasPorUnidade,
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

export async function loadDespesasData(
  portalSlug: string,
  searchParams: DespesasSearchParams,
) {
  const context = parseDespesasContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const portalConfig = await getPortalConfig();

  const [
    metricasGerais,
    impactoLocais,
    concentracao,
    restosResumo,
    despesasUnidades,
    diariasResumo,
    diariasBeneficiarios,
  ] = await Promise.all([
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

  return {
    context,
    metricasGerais,
    impactoLocais,
    concentracao,
    restosResumo,
    despesasUnidades,
    diariasResumo,
    diariasBeneficiarios,
  };
}
