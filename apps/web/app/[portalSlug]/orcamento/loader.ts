import {
  getExecucaoOrcamentaria,
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

export async function loadOrcamentoData(
  portalSlug: string,
  searchParams: OrcamentoSearchParams,
) {
  const context = parseOrcamentoContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const [items, funcionalData] = await Promise.all([
    getExecucaoOrcamentaria(selectedYear, entidadesIds),
    getOrcamentoFuncional(selectedYear, entidadesIds),
  ]);

  return {
    portalSlug,
    context,
    items,
    funcionalData,
    summary: summarizeExecucao(items),
  };
}
