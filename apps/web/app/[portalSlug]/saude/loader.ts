import { getHistoriaSaude, getHistoriaSaudeMetrics } from "@transparencia/db";

export interface SaudeSearchParams {
  ano?: string;
  entidades?: string;
}

export interface SaudeContext {
  selectedYear: number;
  isCurrentYear: boolean;
}

export function parseSaudeContext(
  searchParams: SaudeSearchParams,
): SaudeContext {
  const currentYear = new Date().getFullYear();
  const selectedYear = searchParams.ano
    ? Number(searchParams.ano)
    : currentYear;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
  };
}

function classifyHhi(hhi: number): string {
  if (hhi >= 2500) return "alta";
  if (hhi >= 1500) return "moderada a alta";
  return "baixa";
}

export async function loadSaudeData(
  portalSlug: string,
  searchParams: SaudeSearchParams,
) {
  const context = parseSaudeContext(searchParams);
  const [saudeLegacy, saudeMetrics] = await Promise.all([
    getHistoriaSaude(context.selectedYear),
    getHistoriaSaudeMetrics(portalSlug, context.selectedYear),
  ]);

  // Fallback legado controlado: mantém os blocos narrativos/detalhados que ainda
  // não estão materializados no DTO métrico e sobrepõe apenas campos já cobertos.
  const saude = saudeMetrics
    ? {
        ...saudeLegacy,
        orcamento: {
          ...saudeLegacy.orcamento,
          dotacao: saudeMetrics.dotacaoTotal,
          empenhado: saudeMetrics.totalEmpenhado,
          liquidado: saudeMetrics.totalLiquidado,
          pago: saudeMetrics.totalPago,
          taxaExecucao:
            saudeMetrics.dotacaoTotal > 0
              ? saudeMetrics.totalEmpenhado / saudeMetrics.dotacaoTotal
              : 0,
          alertaSubExecucao:
            saudeMetrics.dotacaoTotal > 0
              ? saudeMetrics.totalEmpenhado / saudeMetrics.dotacaoTotal < 0.7
              : false,
          medicamentosInsumos: saudeMetrics.medicamentosInsumosPago,
        },
        farmaceutica: {
          ...saudeLegacy.farmaceutica,
          medicamentosInsumos: saudeMetrics.medicamentosInsumosPago,
          judicializacao: saudeMetrics.judicializacaoPago,
          hhi: Math.round(saudeMetrics.hhiConcentracaoFornecedores),
          hhiClassificacao: classifyHhi(
            Math.round(saudeMetrics.hhiConcentracaoFornecedores),
          ),
        },
        fontesReceita: {
          ...saudeLegacy.fontesReceita,
          emendasParlamentares: saudeMetrics.emendasSaudeArrecadado,
        },
        emendasStats: {
          ...saudeLegacy.emendasStats,
          totalAutorizado: saudeMetrics.emendasSaudeArrecadado,
          taxaEmpenho:
            saudeMetrics.emendasSaudeArrecadado > 0
              ? saudeLegacy.emendasStats.totalEmpenhado /
                saudeMetrics.emendasSaudeArrecadado
              : 0,
        },
        emendasTotal: saudeMetrics.emendasSaudeArrecadado,
      }
    : saudeLegacy;

  return {
    portalSlug,
    context,
    saude,
  };
}
