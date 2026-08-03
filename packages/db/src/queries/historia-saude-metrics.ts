import { db } from "../client";

export interface HistoriaSaudeMetricsDTO {
  historiaSaudeId: string;
  portalSlug: string;
  ano: number;
  dotacaoTotal: number;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  medicamentosInsumosPago: number;
  judicializacaoPago: number;
  emendasSaudeArrecadado: number;
  hhiConcentracaoFornecedores: number;
}

/**
 * Retorna as métricas da história da saúde para um portal e ano.
 */
export async function getHistoriaSaudeMetrics(
  portalSlug: string,
  ano: number,
): Promise<HistoriaSaudeMetricsDTO | null> {
  const result = await db
    .selectFrom("fct_historia_saude_metricas")
    .selectAll()
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .executeTakeFirst();

  if (!result) return null;

  return {
    historiaSaudeId: result.historia_saude_id,
    portalSlug: result.portal_slug,
    ano: Number(result.ano),
    dotacaoTotal: Number(result.dotacao_total ?? 0),
    totalEmpenhado: Number(result.total_empenhado ?? 0),
    totalLiquidado: Number(result.total_liquidado ?? 0),
    totalPago: Number(result.total_pago ?? 0),
    medicamentosInsumosPago: Number(result.medicamentos_insumos_pago ?? 0),
    judicializacaoPago: Number(result.judicializacao_pago ?? 0),
    emendasSaudeArrecadado: Number(result.emendas_saude_arrecadado ?? 0),
    hhiConcentracaoFornecedores: Number(
      result.hhi_concentracao_fornecedores ?? 0,
    ),
  } satisfies HistoriaSaudeMetricsDTO;
}
