import { db } from "../client";

export interface ReceitaExtraOrcamentariaItemDTO {
  receitaExtraId: string;
  portalSlug: string;
  ano: number;
  empresaId: string;
  descricao: string;
  valorArrecadado: number;
}

export async function getReceitasExtraOrcamentariasList(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<ReceitaExtraOrcamentariaItemDTO[]> {
  if (empresaIds.length === 0) return [];

  const rows = await db
    .selectFrom("fct_receita_extra_orcamentaria")
    .select([
      "receita_extra_id",
      "portal_slug",
      "ano",
      "empresa_id",
      "descricao",
      "valor_arrecadado",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .where("empresa_id", "in", empresaIds)
    .orderBy("valor_arrecadado", "desc")
    .execute();

  return rows.map((row) => ({
    receitaExtraId: row.receita_extra_id,
    portalSlug: row.portal_slug,
    ano: Number(row.ano),
    empresaId: row.empresa_id,
    descricao: row.descricao,
    valorArrecadado: Number(row.valor_arrecadado ?? 0),
  }));
}
