import { getEntidades, getFontesReceitaMetrics } from "@transparencia/db";

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

function mapFontesMetricToLegacy(
  fontes: NonNullable<Awaited<ReturnType<typeof getFontesReceitaMetrics>>>,
  totalPctChange: number | null,
) {
  const receitaPropria = fontes.receitaPropriaArrecadado;
  const transferenciasUniao = fontes.transferenciasUniaoArrecadado;
  const transferenciasEstado = fontes.transferenciasEstadoArrecadado;
  const total = fontes.totalArrecadado;

  const pctPropriaPrevisto =
    fontes.totalPrevisto > 0
      ? (fontes.receitaPropriaPrevisto / fontes.totalPrevisto) * 100
      : 0;

  const pctArrecadado =
    fontes.totalPrevisto > 0
      ? fontes.totalArrecadado / fontes.totalPrevisto
      : 0;

  return {
    ano: fontes.ano,
    receitaPropria,
    transferenciasUniao,
    transferenciasEstado,
    receitaExtraOrcamentariaArrecadado:
      fontes.receitaExtraOrcamentariaArrecadado,
    total,
    pctPropria: fontes.pctPropria,
    pctPropriaPrevisto,
    alertaDependencia: fontes.alertaDependencia,
    receitaPropriaPrevisto: fontes.receitaPropriaPrevisto,
    receitaPropriaArrecadado: fontes.receitaPropriaArrecadado,
    transferenciasUniaoPrevisto: fontes.transferenciasUniaoPrevisto,
    transferenciasUniaoArrecadado: fontes.transferenciasUniaoArrecadado,
    transferenciasEstadoPrevisto: fontes.transferenciasEstadoPrevisto,
    transferenciasEstadoArrecadado: fontes.transferenciasEstadoArrecadado,
    totalPrevisto: fontes.totalPrevisto,
    totalArrecadado: fontes.totalArrecadado,
    pctArrecadado,
    totalPctChange,
    emendasTotalArrecadado: fontes.emendasTotalArrecadado,
    emendasTotalEmpenhado: fontes.emendasTotalEmpenhado,
    emendasPixArrecadado: fontes.emendasPixArrecadado,
    emendasIndividuaisArrecadado: fontes.emendasIndividuaisArrecadado,
    fpmArrecadado: fontes.fpmArrecadado,
    icmsArrecadado: fontes.icmsArrecadado,
    issIptuArrecadado: fontes.issIptuArrecadado,
  };
}

export async function loadReceitasData(
  portalSlug: string,
  searchParams: ReceitasSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parseReceitasContext(searchParams);
  const { selectedYear, entidadesIds } = context;

  const empresaIds = requireEmpresaIdsForMetrics(
    tenantSlug,
    await resolveEmpresaIds(tenantSlug, entidadesIds),
  );

  const [fonteAtual, fonteAnterior] = await Promise.all([
    getFontesReceitaMetrics(tenantSlug, selectedYear, empresaIds),
    getFontesReceitaMetrics(tenantSlug, selectedYear - 1, empresaIds),
  ]);

  const totalPctChange =
    fonteAtual && fonteAnterior && fonteAnterior.totalArrecadado > 0
      ? ((fonteAtual.totalArrecadado - fonteAnterior.totalArrecadado) /
          fonteAnterior.totalArrecadado) *
        100
      : null;

  return {
    portalSlug: tenantSlug,
    context,
    fonte: fonteAtual
      ? mapFontesMetricToLegacy(fonteAtual, totalPctChange)
      : undefined,
  };
}
