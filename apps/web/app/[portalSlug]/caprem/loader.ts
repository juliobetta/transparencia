import { getHistoriaCaprem, getHistoriaCapremMetrics } from "@transparencia/db";

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
  const selectedYear = searchParams.ano
    ? Number(searchParams.ano)
    : currentYear;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
  };
}

export async function loadCapremData(
  portalSlug: string,
  searchParams: CapremSearchParams,
) {
  const context = parseCapremContext(searchParams);
  const [capremLegacy, capremMetrics] = await Promise.all([
    getHistoriaCaprem(portalSlug, context.selectedYear, null),
    getHistoriaCapremMetrics(portalSlug, context.selectedYear),
  ]);

  // Fallback legado controlado: preserva séries/detalhes CAPREM ainda não
  // disponíveis no DTO métrico e substitui apenas blocos já cobertos no mart.
  const caprem = capremMetrics
    ? {
        ...capremLegacy,
        totalEmpenhado: capremMetrics.totalEmpenhado,
        totalLiquidado: capremMetrics.totalLiquidado,
        totalPago: capremMetrics.totalPago,
        taxaExecucao:
          capremMetrics.totalEmpenhado > 0
            ? capremMetrics.totalPago / capremMetrics.totalEmpenhado
            : 0,
        totalAporteAtuarial: capremMetrics.totalAporteExigido,
        totalDividaResgatada: capremMetrics.totalAmortizacaoDivida,
        totalCaspPlanoSaude: capremMetrics.totalCaspPlanoSaude,
        actuarialRisk: {
          ...capremLegacy.actuarialRisk,
          totalAporteExigido: capremMetrics.totalAporteExigido,
          totalAporteQuitado: capremMetrics.totalAporteQuitado,
          romboAporteNaoRepassado: Math.max(
            0,
            capremMetrics.totalAporteExigido - capremMetrics.totalAporteQuitado,
          ),
          taxaAdimplenciaAporte: capremMetrics.taxaAdimplenciaAporte,
          totalEmpenhadoPatronal: capremMetrics.totalEmpenhadoPatronal,
          totalPagoPatronal: capremMetrics.totalPagoPatronal,
          romboPatronalNaoRepassado: capremMetrics.romboPatronalNaoRepassado,
          totalAmortizacaoDivida: capremMetrics.totalAmortizacaoDivida,
        },
      }
    : capremLegacy;

  return {
    context,
    caprem,
  };
}
