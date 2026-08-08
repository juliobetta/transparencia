import {
  getCapremActuarialTrendMetrics,
  getCapremCadprevMetrics,
  getCapremEntidadesMetrics,
  getCapremNaturezaMetrics,
  getHistoriaCapremMetrics,
} from "@transparencia/db";

export interface CapremSearchParams {
  ano?: string;
  empresa?: string;
}

export interface CapremContext {
  selectedYear: number;
  isCurrentYear: boolean;
}

export function parseCapremContext(
  searchParams: CapremSearchParams,
): CapremContext {
  const currentYear = new Date().getFullYear();
  const parsed = searchParams.ano ? Number(searchParams.ano) : currentYear;
  const selectedYear =
    Number.isInteger(parsed) && parsed > 1900 ? parsed : currentYear;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
  };
}

function requirePortalSlug(portalSlug: string): string {
  const normalized = portalSlug.trim();
  if (!normalized) {
    throw new Error("portalSlug vazio: o tenant deve ser informado.");
  }
  if (normalized === "porciuncula") {
    return "porciuncula_prefeitura";
  }
  return normalized;
}

export async function loadCapremData(
  portalSlug: string,
  searchParams: CapremSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parseCapremContext(searchParams);

  const [
    capremMetrics,
    entidadesMetrics,
    naturezaMetrics,
    actuarialTrend,
    cadprevParcelamentos,
  ] = await Promise.all([
    getHistoriaCapremMetrics(tenantSlug, context.selectedYear),
    getCapremEntidadesMetrics(tenantSlug, context.selectedYear),
    getCapremNaturezaMetrics(tenantSlug, context.selectedYear),
    getCapremActuarialTrendMetrics(tenantSlug),
    getCapremCadprevMetrics(tenantSlug, context.selectedYear),
  ]);

  const totalEmpenhado = capremMetrics?.totalEmpenhado ?? 0;
  const totalLiquidado = capremMetrics?.totalLiquidado ?? 0;
  const totalPago = capremMetrics?.totalPago ?? 0;
  const totalAporteExigido = capremMetrics?.totalAporteExigido ?? 0;
  const totalAporteQuitado = capremMetrics?.totalAporteQuitado ?? 0;
  const totalEmpenhadoPatronal = capremMetrics?.totalEmpenhadoPatronal ?? 0;
  const totalPagoPatronal = capremMetrics?.totalPagoPatronal ?? 0;
  const totalAmortizacaoDivida = capremMetrics?.totalAmortizacaoDivida ?? 0;
  const totalCaspPlanoSaude = capremMetrics?.totalCaspPlanoSaude ?? 0;
  const servidoresEfetivos = capremMetrics?.servidoresEfetivos ?? 0;
  const servidoresTemporarios = capremMetrics?.servidoresTemporarios ?? 0;

  const romboAporteNaoRepassado = Math.max(
    0,
    totalAporteExigido - totalAporteQuitado,
  );
  const romboPatronalNaoRepassado = Math.max(
    0,
    totalEmpenhadoPatronal - totalPagoPatronal,
  );
  const taxaAdimplenciaAporte =
    totalAporteExigido > 0
      ? (totalAporteQuitado / totalAporteExigido) * 100
      : 100;
  const currentYear = new Date().getFullYear();
  const mesesDecorridos =
    context.selectedYear < currentYear
      ? 12
      : Math.max(1, new Date().getMonth() + 1);
  const deficitMedioMensal =
    romboPatronalNaoRepassado > 0
      ? romboPatronalNaoRepassado / mesesDecorridos
      : 0;

  const currTrend = actuarialTrend.find((t) => t.ano === context.selectedYear);
  const prevTrend = actuarialTrend.find(
    (t) => t.ano === context.selectedYear - 1,
  );
  const prevAmort = prevTrend?.amortizacaoDivida ?? 0;
  const currAmort = currTrend?.amortizacaoDivida ?? totalAmortizacaoDivida;
  const variacaoAmortizacaoPct =
    prevAmort > 0
      ? ((currAmort - prevAmort) / prevAmort) * 100
      : currAmort > 0
        ? 100
        : 0;

  const caprem = {
    entidades: entidadesMetrics,
    natureza: naturezaMetrics,
    cadprevParcelamentos,
    actuarialTrend,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    taxaExecucao: totalEmpenhado > 0 ? totalPago / totalEmpenhado : 0,
    totalAporteAtuarial: totalAporteExigido,
    totalDividaResgatada: totalAmortizacaoDivida,
    totalCaspPlanoSaude,
    actuarialRisk: {
      totalAporteExigido,
      totalAporteQuitado,
      romboAporteNaoRepassado,
      taxaAdimplenciaAporte,
      totalEmpenhadoPatronal,
      totalPagoPatronal,
      romboPatronalNaoRepassado,
      deficitMedioMensal,
      totalAmortizacaoDivida,
      variacaoAmortizacaoPct,
      servidoresEfetivos,
      servidoresTemporariosComissionados: servidoresTemporarios,
      razaoTemporariosEfetivosPct:
        servidoresEfetivos > 0
          ? (servidoresTemporarios / servidoresEfetivos) * 100
          : 0,
    },
  };

  return {
    context,
    caprem,
  };
}
