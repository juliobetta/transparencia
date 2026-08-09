import { db } from "../client";

/**
 * DTO de métricas consolidadas de posição fiscal.
 *
 * Não expõe `empresa_id` nem `posicao_fiscal_id` intencionalmente:
 * - `empresa_id` é ambíguo na visão consolidada (N empresas selecionadas).
 * - `posicao_fiscal_id` é PK interna do mart, sem valor para o consumidor.
 * O chamador já conhece as empresas selecionadas via `empresaIds`.
 */
export interface PosicaoFiscalMetricsDTO {
  portalSlug: string;
  ano: number;
  totalArrecadado: number;
  despesasPagas: number;
  restosPagosNoAno: number;
  restosPendentesAdmAnterior: number;
  restosPendentesAdmAtual: number;
  saldoEstimado: number;
}

/**
 * Retorna as métricas de posição fiscal consolidadas para as empresas selecionadas.
 *
 * - `empresaIds` é obrigatório e deve ter pelo menos 1 elemento.
 * - Quando múltiplas empresas são passadas, os campos numéricos são somados (SUM),
 *   refletindo a visão agregada do conjunto selecionado.
 * - Retorna `null` se `empresaIds` estiver vazio ou se não houver dados no mart.
 */
export async function getPosicaoFiscalMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<PosicaoFiscalMetricsDTO | null> {
  if (empresaIds.length === 0) return null;

  const result = await db
    .selectFrom("fct_posicao_fiscal_metricas")
    .select((eb) => [
      "portal_slug",
      "ano",
      eb.fn.sum<string>("total_arrecadado").as("total_arrecadado"),
      eb.fn.sum<string>("despesas_pagas").as("despesas_pagas"),
      eb.fn.sum<string>("restos_pagos_no_ano").as("restos_pagos_no_ano"),
      eb.fn
        .sum<string>("restos_pendentes_adm_anterior")
        .as("restos_pendentes_adm_anterior"),
      eb.fn
        .sum<string>("restos_pendentes_adm_atual")
        .as("restos_pendentes_adm_atual"),
      eb.fn.sum<string>("saldo_estimado").as("saldo_estimado"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .where("empresa_id", "in", empresaIds)
    .groupBy(["portal_slug", "ano"])
    .executeTakeFirst();

  if (!result) return null;

  return {
    portalSlug: result.portal_slug,
    ano: Number(result.ano),
    totalArrecadado: Number(result.total_arrecadado ?? 0),
    despesasPagas: Number(result.despesas_pagas ?? 0),
    restosPagosNoAno: Number(result.restos_pagos_no_ano ?? 0),
    restosPendentesAdmAnterior: Number(
      result.restos_pendentes_adm_anterior ?? 0,
    ),
    restosPendentesAdmAtual: Number(result.restos_pendentes_adm_atual ?? 0),
    saldoEstimado: Number(result.saldo_estimado ?? 0),
  } satisfies PosicaoFiscalMetricsDTO;
}
