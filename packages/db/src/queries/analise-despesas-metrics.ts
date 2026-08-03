import { db } from "../client";

/**
 * DTO de métricas consolidadas de análise de despesas.
 *
 * Não expõe `empresa_id` nem `analise_despesas_id` intencionalmente:
 * - `empresa_id` é ambíguo na visão consolidada (N empresas selecionadas).
 * - `analise_despesas_id` é PK interna do mart por empresa.
 * O chamador já conhece as empresas selecionadas via `empresaIds`.
 */
export interface AnaliseDespesasMetricsDTO {
  portalSlug: string;
  ano: number;
  orgaoCodigo: string;
  unidadeCodigo: string;
  funcaoCodigo: string;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
}

/**
 * Retorna as métricas de análise de despesas consolidadas por órgão/unidade/função para as empresas selecionadas.
 *
 * - `empresaIds` é obrigatório e deve ter pelo menos 1 elemento.
 * - Quando múltiplas empresas são passadas, os valores numéricos são somados (SUM),
 *   refletindo a visão agregada do conjunto de empresas selecionadas.
 * - Retorna `[]` se `empresaIds` estiver vazio.
 */
export async function getAnaliseDespesasMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<AnaliseDespesasMetricsDTO[]> {
  if (empresaIds.length === 0) return [];

  const results = await db
    .selectFrom("fct_analise_despesas_metricas")
    .select((eb) => [
      "portal_slug",
      "ano",
      "orgao_codigo",
      "unidade_codigo",
      "funcao_codigo",
      eb.fn.sum<string>("total_empenhado").as("total_empenhado"),
      eb.fn.sum<string>("total_liquidado").as("total_liquidado"),
      eb.fn.sum<string>("total_pago").as("total_pago"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .where("empresa_id", "in", empresaIds)
    .groupBy([
      "portal_slug",
      "ano",
      "orgao_codigo",
      "unidade_codigo",
      "funcao_codigo",
    ])
    .execute();

  return results.map(
    (r) =>
      ({
        portalSlug: r.portal_slug,
        ano: Number(r.ano),
        orgaoCodigo: r.orgao_codigo,
        unidadeCodigo: r.unidade_codigo,
        funcaoCodigo: r.funcao_codigo,
        totalEmpenhado: Number(r.total_empenhado ?? 0),
        totalLiquidado: Number(r.total_liquidado ?? 0),
        totalPago: Number(r.total_pago ?? 0),
      }) satisfies AnaliseDespesasMetricsDTO,
  );
}
