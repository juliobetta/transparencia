import {
  getDepartmentalPayrollMetrics,
  getDistribuicaoProventosMetrics,
  getEntidades,
  getExecucaoDecimoTerceiroMetrics,
  getFolhaVsServicosMetrics,
  getPercentualChefiasEfetivasMetrics,
} from "@transparencia/db";

export interface PessoalSearchParams {
  ano?: string;
  entidades?: string;
}

export interface PessoalContext {
  selectedYear: number;
  isCurrentYear: boolean;
  entidadesIds?: string[];
}

export function parsePessoalContext(
  searchParams: PessoalSearchParams,
): PessoalContext {
  const currentYear = new Date().getFullYear();
  const parsedYear = searchParams?.ano ? Number(searchParams.ano) : NaN;
  const selectedYear =
    !Number.isNaN(parsedYear) && parsedYear > 1900 ? parsedYear : currentYear;
  const entidadesIds = searchParams?.entidades
    ? searchParams.entidades.split(",").filter(Boolean)
    : undefined;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
    entidadesIds,
  };
}

function requirePortalSlug(portalSlug: string): string {
  if (!portalSlug || typeof portalSlug !== "string") {
    throw new Error("portalSlug vazio: o tenant deve ser informado.");
  }
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

export async function loadPessoalData(
  portalSlug: string,
  searchParams: PessoalSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parsePessoalContext(searchParams);
  const { selectedYear, entidadesIds } = context;
  const empresaIds = await resolveEmpresaIds(tenantSlug, entidadesIds);

  const [
    folhaData,
    pctChefias,
    decimo13,
    distribuicaoProventos,
    departmentalPayroll,
  ] = await Promise.all([
    getFolhaVsServicosMetrics({
      years: [selectedYear],
      empresaIds,
      portalSlug: tenantSlug,
    }),
    getPercentualChefiasEfetivasMetrics(tenantSlug, selectedYear, empresaIds),
    getExecucaoDecimoTerceiroMetrics(tenantSlug, selectedYear, empresaIds),
    getDistribuicaoProventosMetrics(tenantSlug, selectedYear, empresaIds),
    getDepartmentalPayrollMetrics(tenantSlug, selectedYear, empresaIds),
  ]);

  return {
    context,
    folhaData,
    pctChefias,
    decimo13,
    distribuicaoProventos,
    departmentalPayroll,
  };
}
