import {
  getDepartmentalPayroll,
  getDistribuicaoProventos,
  getEntidades,
  getExecucaoDecimoTerceiro,
  getFolhaVsServicos,
  getPercentualChefiasEfetivas,
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
    getFolhaVsServicos({
      years: [selectedYear],
      empresaIds,
      portalSlug: tenantSlug,
    }),
    getPercentualChefiasEfetivas(selectedYear, empresaIds),
    getExecucaoDecimoTerceiro(selectedYear, empresaIds),
    getDistribuicaoProventos(selectedYear),
    getDepartmentalPayroll(selectedYear, empresaIds),
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
