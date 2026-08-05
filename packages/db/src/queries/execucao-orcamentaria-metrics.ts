import { db } from "../client";

/**
 * DTO de métricas consolidadas de execução orçamentária.
 *
 * Não expõe `empresa_id` nem `execucao_orcamentaria_id` intencionalmente:
 * - `empresa_id` é ambíguo na visão consolidada (N empresas selecionadas).
 * - `execucao_orcamentaria_id` é PK interna do mart por empresa.
 * O chamador já conhece as empresas selecionadas via `empresaIds`.
 */
export interface ExecucaoOrcamentariaMetricsDTO {
  portalSlug: string;
  ano: number;
  orgaoCodigo: string;
  orgaoNome?: string;
  unidadeCodigo: string;
  funcaoCodigo: string;
  subfuncaoCodigo: string;
  totalDotacaoAtualizada: number;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  saldoOrcamentario: number;
  taxaExecucao: number;
  alertaExecucao: "normal" | "N/D" | "excesso" | "baixa";
}

/**
 * Retorna as métricas de execução orçamentária consolidadas por órgão/unidade/função/subfunção para as empresas selecionadas.
 *
 * - `empresaIds` é obrigatório e deve ter pelo menos 1 elemento.
 * - Quando múltiplas empresas são passadas, os valores numéricos são somados (SUM)
 *   e a taxa/alerta de execução é recalculada para refletir a visão agregada.
 * - Retorna `[]` se `empresaIds` estiver vazio.
 */
export async function getExecucaoOrcamentariaMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<ExecucaoOrcamentariaMetricsDTO[]> {
  if (empresaIds.length === 0) return [];

  const results = await db
    .selectFrom("fct_execucao_orcamentaria_metricas")
    .select((eb) => [
      "portal_slug",
      "ano",
      "orgao_codigo",
      eb.fn.max("orgao_nome").as("orgao_nome"),
      "unidade_codigo",
      "funcao_codigo",
      "subfuncao_codigo",
      eb.fn
        .sum<string>("total_dotacao_atualizada")
        .as("total_dotacao_atualizada"),
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
      "subfuncao_codigo",
    ])
    .execute();

  return results.map((r) => {
    const totalDotacaoAtualizada = Number(r.total_dotacao_atualizada ?? 0);
    const totalEmpenhado = Number(r.total_empenhado ?? 0);
    const totalLiquidado = Number(r.total_liquidado ?? 0);
    const totalPago = Number(r.total_pago ?? 0);
    const saldoOrcamentario = totalDotacaoAtualizada - totalEmpenhado;
    const taxaExecucao =
      totalDotacaoAtualizada > 0 ? totalEmpenhado / totalDotacaoAtualizada : 0;

    let alertaExecucao: "normal" | "N/D" | "excesso" | "baixa" = "normal";
    if (totalEmpenhado === 0 && totalDotacaoAtualizada === 0) {
      alertaExecucao = "N/D";
    } else if (totalDotacaoAtualizada === 0 && totalEmpenhado > 0) {
      alertaExecucao = "excesso";
    } else if (taxaExecucao < 0.3) {
      alertaExecucao = "baixa";
    } else if (taxaExecucao > 1.0) {
      alertaExecucao = "excesso";
    }

    return {
      portalSlug: r.portal_slug,
      ano: Number(r.ano),
      orgaoCodigo: r.orgao_codigo,
      orgaoNome: r.orgao_nome ?? undefined,
      unidadeCodigo: r.unidade_codigo,
      funcaoCodigo: r.funcao_codigo,
      subfuncaoCodigo: r.subfuncao_codigo,
      totalDotacaoAtualizada,
      totalEmpenhado,
      totalLiquidado,
      totalPago,
      saldoOrcamentario,
      taxaExecucao,
      alertaExecucao,
    } satisfies ExecucaoOrcamentariaMetricsDTO;
  });
}
