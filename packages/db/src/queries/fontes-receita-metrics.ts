import { db } from "../client";

/**
 * DTO de métricas consolidadas de fontes de receita.
 *
 * Não expõe `empresa_id` nem `fontes_receita_id` intencionalmente:
 * - `empresa_id` é ambíguo na visão consolidada (N empresas selecionadas).
 * - `fontes_receita_id` é PK interna do mart por empresa.
 * O chamador já conhece as empresas selecionadas via `empresaIds`.
 */
export interface FontesReceitaMetricsDTO {
  portalSlug: string;
  ano: number;
  receitaPropriaPrevisto: number;
  receitaPropriaArrecadado: number;
  transferenciasUniaoPrevisto: number;
  transferenciasUniaoArrecadado: number;
  transferenciasEstadoPrevisto: number;
  transferenciasEstadoArrecadado: number;
  totalPrevisto: number;
  totalArrecadado: number;
  pctPropria: number;
  alertaDependencia: boolean;
  fpmArrecadado: number;
  icmsArrecadado: number;
  issIptuArrecadado: number;
  emendasPixArrecadado: number;
  emendasIndividuaisArrecadado: number;
  emendasTotalArrecadado: number;
}

/**
 * Retorna as métricas de fontes de receita consolidadas para as empresas selecionadas.
 *
 * - `empresaIds` é obrigatório e deve ter pelo menos 1 elemento.
 * - Quando múltiplas empresas são passadas, os valores numéricos são somados (SUM)
 *   e a porcentagem de receita própria e o alerta de dependência são recalculados para o conjunto selecionado.
 * - Retorna `null` se `empresaIds` estiver vazio ou se não houver dados no mart.
 */
export async function getFontesReceitaMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<FontesReceitaMetricsDTO | null> {
  if (empresaIds.length === 0) return null;

  const result = await db
    .selectFrom("fct_fontes_receita_metricas")
    .select((eb) => [
      "portal_slug",
      "ano",
      eb.fn
        .sum<string>("receita_propria_previsto")
        .as("receita_propria_previsto"),
      eb.fn
        .sum<string>("receita_propria_arrecadado")
        .as("receita_propria_arrecadado"),
      eb.fn
        .sum<string>("transferencias_uniao_previsto")
        .as("transferencias_uniao_previsto"),
      eb.fn
        .sum<string>("transferencias_uniao_arrecadado")
        .as("transferencias_uniao_arrecadado"),
      eb.fn
        .sum<string>("transferencias_estado_previsto")
        .as("transferencias_estado_previsto"),
      eb.fn
        .sum<string>("transferencias_estado_arrecadado")
        .as("transferencias_estado_arrecadado"),
      eb.fn.sum<string>("total_previsto").as("total_previsto"),
      eb.fn.sum<string>("total_arrecadado").as("total_arrecadado"),
      eb.fn.sum<string>("fpm_arrecadado").as("fpm_arrecadado"),
      eb.fn.sum<string>("icms_arrecadado").as("icms_arrecadado"),
      eb.fn.sum<string>("iss_iptu_arrecadado").as("iss_iptu_arrecadado"),
      eb.fn.sum<string>("emendas_pix_arrecadado").as("emendas_pix_arrecadado"),
      eb.fn
        .sum<string>("emendas_individuais_arrecadado")
        .as("emendas_individuais_arrecadado"),
      eb.fn
        .sum<string>("emendas_total_arrecadado")
        .as("emendas_total_arrecadado"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .where("empresa_id", "in", empresaIds)
    .groupBy(["portal_slug", "ano"])
    .executeTakeFirst();

  if (!result) return null;

  const receitaPropriaArrecadado = Number(
    result.receita_propria_arrecadado ?? 0,
  );
  const totalArrecadado = Number(result.total_arrecadado ?? 0);
  const receitaPropriaPrevisto = Number(result.receita_propria_previsto ?? 0);
  const totalPrevisto = Number(result.total_previsto ?? 0);

  const rawPctPropria =
    totalArrecadado > 0
      ? (receitaPropriaArrecadado / totalArrecadado) * 100
      : totalPrevisto > 0
        ? (receitaPropriaPrevisto / totalPrevisto) * 100
        : 0;

  // Garante intervalo [0, 100] — estornos ou devoluções no mart podem
  // produzir receitaPropria > total ou valores negativos pontualmente.
  const pctPropria = Math.min(100, Math.max(0, rawPctPropria));

  const alertaDependencia = pctPropria < 10;

  return {
    portalSlug: result.portal_slug,
    ano: Number(result.ano),
    receitaPropriaPrevisto,
    receitaPropriaArrecadado,
    transferenciasUniaoPrevisto: Number(
      result.transferencias_uniao_previsto ?? 0,
    ),
    transferenciasUniaoArrecadado: Number(
      result.transferencias_uniao_arrecadado ?? 0,
    ),
    transferenciasEstadoPrevisto: Number(
      result.transferencias_estado_previsto ?? 0,
    ),
    transferenciasEstadoArrecadado: Number(
      result.transferencias_estado_arrecadado ?? 0,
    ),
    totalPrevisto,
    totalArrecadado,
    pctPropria,
    alertaDependencia,
    fpmArrecadado: Number(result.fpm_arrecadado ?? 0),
    icmsArrecadado: Number(result.icms_arrecadado ?? 0),
    issIptuArrecadado: Number(result.iss_iptu_arrecadado ?? 0),
    emendasPixArrecadado: Number(result.emendas_pix_arrecadado ?? 0),
    emendasIndividuaisArrecadado: Number(
      result.emendas_individuais_arrecadado ?? 0,
    ),
    emendasTotalArrecadado: Number(result.emendas_total_arrecadado ?? 0),
  } satisfies FontesReceitaMetricsDTO;
}
