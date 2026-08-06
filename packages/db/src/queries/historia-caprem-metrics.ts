import { db } from "../client";

export interface HistoriaCapremMetricsDTO {
  historiaCapremId: string;
  portalSlug: string;
  ano: number;
  totalAporteExigido: number;
  totalAporteQuitado: number;
  taxaAdimplenciaAporte: number;
  totalEmpenhadoPatronal: number;
  totalPagoPatronal: number;
  romboPatronalNaoRepassado: number;
  totalAmortizacaoDivida: number;
  totalCaspPlanoSaude: number;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  servidoresEfetivos: number;
  servidoresTemporarios: number;
}

/**
 * Retorna as métricas da história previdenciária (CAPREM) para o portal de Porciúncula e ano.
 *
 * A história da CAPREM é um apanhado geral atômico exclusivo da Prefeitura de Porciúncula,
 * não possuindo filtro por `empresaIds` (consolida todas as entidades) e retornando `null`
 * para qualquer outro portal.
 */
export async function getHistoriaCapremMetrics(
  portalSlug: string,
  ano: number,
): Promise<HistoriaCapremMetricsDTO | null> {
  const result = await db
    .selectFrom("fct_historia_caprem_metricas")
    .selectAll()
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .executeTakeFirst();

  if (!result) return null;

  return {
    historiaCapremId: result.historia_caprem_id,
    portalSlug: result.portal_slug,
    ano: Number(result.ano),
    totalAporteExigido: Number(result.total_aporte_exigido ?? 0),
    totalAporteQuitado: Number(result.total_aporte_quitado ?? 0),
    taxaAdimplenciaAporte: Number(result.taxa_adimplencia_aporte ?? 0),
    totalEmpenhadoPatronal: Number(result.total_empenhado_patronal ?? 0),
    totalPagoPatronal: Number(result.total_pago_patronal ?? 0),
    romboPatronalNaoRepassado: Number(result.rombo_patronal_nao_repassado ?? 0),
    totalAmortizacaoDivida: Number(result.total_amortizacao_divida ?? 0),
    totalCaspPlanoSaude: Number(result.total_casp_plano_saude ?? 0),
    totalEmpenhado: Number(result.total_empenhado ?? 0),
    totalLiquidado: Number(result.total_liquidado ?? 0),
    totalPago: Number(result.total_pago ?? 0),
    servidoresEfetivos: Number(result.servidores_efetivos ?? 0),
    servidoresTemporarios: Number(result.servidores_temporarios ?? 0),
  } satisfies HistoriaCapremMetricsDTO;
}

export interface EntityCapremDTO {
  entidade: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  taxaExecucao: number;
}

export async function getCapremEntidadesMetrics(
  portalSlug: string,
  ano: number,
): Promise<EntityCapremDTO[]> {
  try {
    const rows = await db
      .selectFrom("fct_caprem_entidades_metricas")
      .select(["entidade", "empenhado", "liquidado", "pago", "taxa_execucao"])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .orderBy("empenhado", "desc")
      .execute();

    return rows.map((r) => ({
      entidade: r.entidade ?? "",
      empenhado: Number(r.empenhado ?? 0),
      liquidado: Number(r.liquidado ?? 0),
      pago: Number(r.pago ?? 0),
      taxaExecucao: Number(r.taxa_execucao ?? 0),
    }));
  } catch {
    return [];
  }
}
