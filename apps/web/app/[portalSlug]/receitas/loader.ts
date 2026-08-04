import { getFontesReceita, getPortalConfig } from "@transparencia/db";

export interface ReceitasSearchParams {
  ano?: string;
  entidades?: string;
}

export interface ReceitasContext {
  selectedYear: number;
  isCurrentYear: boolean;
  entidadesIds?: string[];
}

export function parseReceitasContext(
  searchParams: ReceitasSearchParams,
): ReceitasContext {
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

export async function loadReceitasData(searchParams: ReceitasSearchParams) {
  const context = parseReceitasContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const [_portalConfig, fontes] = await Promise.all([
    getPortalConfig(),
    getFontesReceita([selectedYear], entidadesIds),
  ]);

  return {
    context,
    fonte: fontes[0],
  };
}
