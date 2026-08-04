import {
  getDepartmentalPayroll,
  getDistribuicaoProventos,
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

export async function loadPessoalData(
  portalSlug: string,
  searchParams: PessoalSearchParams,
) {
  const context = parsePessoalContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const [
    folhaData,
    pctChefias,
    decimo13,
    distribuicaoProventos,
    departmentalPayroll,
  ] = await Promise.all([
    getFolhaVsServicos({
      years: [selectedYear],
      empresaIds: entidadesIds,
      portalSlug,
    }),
    getPercentualChefiasEfetivas(selectedYear, entidadesIds),
    getExecucaoDecimoTerceiro(selectedYear, entidadesIds),
    getDistribuicaoProventos(selectedYear),
    getDepartmentalPayroll(selectedYear, entidadesIds),
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
