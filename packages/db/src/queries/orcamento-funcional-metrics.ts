import { db } from "../client";

export interface OrcamentoFuncionalMetricsDTO {
  funcaoNome: string;
  subfuncaoNome: string;
  dotacaoAtualizada: number;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export async function getOrcamentoFuncionalMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<OrcamentoFuncionalMetricsDTO[]> {
  if (empresaIds.length === 0) return [];

  const results = await db
    .selectFrom("fct_orcamento_funcional_metricas")
    .select([
      "funcao_nome",
      "subfuncao_nome",
      "dotacao_atualizada",
      "empenhado",
      "liquidado",
      "pago",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .where("empresa_id", "in", empresaIds)
    .execute();

  return results.map((row) => ({
    funcaoNome: row.funcao_nome ?? "",
    subfuncaoNome: row.subfuncao_nome ?? "",
    dotacaoAtualizada: Number(row.dotacao_atualizada ?? 0),
    empenhado: Number(row.empenhado ?? 0),
    liquidado: Number(row.liquidado ?? 0),
    pago: Number(row.pago ?? 0),
  }));
}
