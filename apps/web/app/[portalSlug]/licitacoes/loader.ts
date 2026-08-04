import {
  getAdesaoDeAta,
  getAdesaoExterna,
  getAnomaliasContratuais,
  getDistribucaoModalidades,
  getLicitacaoGaps,
} from "@transparencia/db";

export interface LicitacoesSearchParams {
  ano?: string;
  entidades?: string;
}

export interface LicitacoesContext {
  selectedYear: number;
  isCurrentYear: boolean;
  entidadesIds?: string[];
}

export function parseLicitacoesContext(
  searchParams: LicitacoesSearchParams,
): LicitacoesContext {
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

export async function loadLicitacoesData(
  portalSlug: string,
  searchParams: LicitacoesSearchParams,
) {
  const context = parseLicitacoesContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const [gaps, adesao, adesaoExterna, anomalias, modalidades] =
    await Promise.all([
      getLicitacaoGaps(selectedYear, entidadesIds),
      getAdesaoDeAta(selectedYear, entidadesIds),
      getAdesaoExterna(selectedYear, entidadesIds),
      getAnomaliasContratuais(selectedYear, entidadesIds),
      getDistribucaoModalidades(selectedYear, entidadesIds),
    ]);

  return {
    portalSlug,
    context,
    gaps,
    adesao,
    adesaoExterna,
    anomalias,
    modalidades,
  };
}
