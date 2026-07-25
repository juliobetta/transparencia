import { sql } from "kysely";
import { db } from "../client";

export interface FontesReceitaRecord {
  ano: number;
  receita_propria: number;
  transferencias_uniao: number;
  transferencias_estado: number;
  total: number;
  pct_propria: number;
  pct_propria_previsto: number;
  alerta_dependencia: boolean;
  receita_propria_previsto: number;
  receita_propria_arrecadado: number;
  transferencias_uniao_previsto: number;
  transferencias_uniao_arrecadado: number;
  transferencias_estado_previsto: number;
  transferencias_estado_arrecadado: number;
  total_previsto: number;
  total_arrecadado: number;
  pct_arrecadado: number;
  total_pct_change?: number | null;
}

const INTRA_PREFIXES = ["17", "27"];

async function sumColumn(
  tipoReceita: string,
  col: "previsao_atualizada" | "arrecadado",
  year: number,
  rootOnly: boolean = false,
  empresaIds?: string[] | null,
): Promise<number> {
  let query = sql`
    SELECT ${sql.ref(col)} AS val
    FROM fct_receitas t
    WHERE t.tipo_receita = ${tipoReceita}
      AND t.ano = ${year}
  `;

  if (empresaIds && empresaIds.length > 0) {
    query = sql`${query} AND t.empresa_id = ANY(${empresaIds})`;
  }

  if (tipoReceita === "orcamentaria" && empresaIds && empresaIds.length > 1) {
    const conditions = INTRA_PREFIXES.map((p) => `t.codigo LIKE '${p}%'`).join(
      " OR ",
    );
    query = sql`${query} AND NOT (${sql.raw(conditions)})`;
  }

  if (rootOnly) {
    query = sql`${query} AND NOT EXISTS (
      SELECT 1 FROM fct_receitas t2
      WHERE t2.tipo_receita = t.tipo_receita
        AND t2.ano = ${year}
        AND t2.empresa_id = t.empresa_id
        AND t2.codigo != t.codigo
        AND t.codigo LIKE RTRIM(t2.codigo, '0.') || '%'
        AND LENGTH(RTRIM(t2.codigo, '0.')) < LENGTH(RTRIM(t.codigo, '0.'))
    )`;
  }

  try {
    const res = await query.execute(db);
    if (!res.rows || res.rows.length === 0) return 0;
    let sum = 0;
    for (const row of res.rows as any[]) {
      const valStr = String(row.val ?? "0").replace(",", ".");
      const num = parseFloat(valStr);
      if (!Number.isNaN(num)) sum += num;
    }
    return sum;
  } catch {
    return 0;
  }
}

export async function getFontesReceita(
  years: number[],
  empresaIds?: string[] | null,
): Promise<FontesReceitaRecord[]> {
  const records: FontesReceitaRecord[] = [];

  for (const year of years) {
    const total_previsto = await sumColumn(
      "orcamentaria",
      "previsao_atualizada",
      year,
      true,
      empresaIds,
    );
    const total_arrecadado = await sumColumn(
      "orcamentaria",
      "arrecadado",
      year,
      true,
      empresaIds,
    );

    const uniao_previsto = await sumColumn(
      "uniao",
      "previsao_atualizada",
      year,
      true,
      empresaIds,
    );
    const uniao_arrecadado = await sumColumn(
      "uniao",
      "arrecadado",
      year,
      true,
      empresaIds,
    );

    const estado_previsto = await sumColumn(
      "estado",
      "previsao_atualizada",
      year,
      true,
      empresaIds,
    );
    const estado_arrecadado = await sumColumn(
      "estado",
      "arrecadado",
      year,
      true,
      empresaIds,
    );

    const propria_previsto = Math.max(
      0,
      total_previsto - uniao_previsto - estado_previsto,
    );
    const propria_arrecadado = Math.max(
      0,
      total_arrecadado - uniao_arrecadado - estado_arrecadado,
    );

    const pct_previsto =
      total_previsto > 0 ? (propria_previsto / total_previsto) * 100 : 0;
    const pct =
      total_arrecadado > 0
        ? (propria_arrecadado / total_arrecadado) * 100
        : pct_previsto;

    records.push({
      ano: year,
      receita_propria: propria_arrecadado,
      transferencias_uniao: uniao_arrecadado,
      transferencias_estado: estado_arrecadado,
      total: total_arrecadado,
      pct_propria: pct,
      pct_propria_previsto: pct_previsto,
      alerta_dependencia: pct < 10,
      receita_propria_previsto: propria_previsto,
      receita_propria_arrecadado: propria_arrecadado,
      transferencias_uniao_previsto: uniao_previsto,
      transferencias_uniao_arrecadado: uniao_arrecadado,
      transferencias_estado_previsto: estado_previsto,
      transferencias_estado_arrecadado: estado_arrecadado,
      total_previsto,
      total_arrecadado,
      pct_arrecadado:
        total_previsto > 0 ? total_arrecadado / total_previsto : 0,
    });
  }

  for (let i = 0; i < records.length; i++) {
    if (i === 0) {
      records[i].total_pct_change = null;
    } else {
      const prevTotal = records[i - 1].total;
      records[i].total_pct_change =
        prevTotal > 0
          ? ((records[i].total - prevTotal) / prevTotal) * 100
          : null;
    }
  }

  return records;
}
