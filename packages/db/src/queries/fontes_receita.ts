import { sql } from "kysely";
import { db } from "../client";

export interface FontesReceitaRecord {
  ano: number;
  receitaPropria: number;
  transferenciasUniao: number;
  transferenciasEstado: number;
  total: number;
  pctPropria: number;
  pctPropriaPrevisto: number;
  alertaDependencia: boolean;
  receitaPropriaPrevisto: number;
  receitaPropriaArrecadado: number;
  transferenciasUniaoPrevisto: number;
  transferenciasUniaoArrecadado: number;
  transferenciasEstadoPrevisto: number;
  transferenciasEstadoArrecadado: number;
  totalPrevisto: number;
  totalArrecadado: number;
  pctArrecadado: number;
  totalPctChange?: number | null;
  emendasTotalArrecadado: number;
  emendasPixArrecadado: number;
  emendasIndividuaisArrecadado: number;
  fpmArrecadado: number;
  icmsArrecadado: number;
  issIptuArrecadado: number;
}

const INTRA_PREFIXES = ["17", "27"];

async function sumColumn({
  tipoReceita,
  col,
  year,
  rootOnly = false,
  notTransfer = false,
  empresaIds,
}: {
  tipoReceita: string;
  col: "previsao_atualizada" | "arrecadado";
  year: number;
  rootOnly?: boolean;
  notTransfer?: boolean;
  empresaIds?: string[] | null;
}): Promise<number> {
  let query = sql`
    SELECT ${sql.ref(col)} AS val
    FROM fct_receitas t
    WHERE t.tipo_receita = ${tipoReceita}
      AND t.ano = ${year}
  `;

  if (notTransfer) {
    query = sql`${query} AND NOT (t.codigo LIKE '1.7%' OR t.codigo LIKE '2.4%')`;
  }

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
    for (const row of res.rows as { val?: unknown }[]) {
      const valStr = String(row.val ?? "0").replace(",", ".");
      const num = parseFloat(valStr);
      if (!Number.isNaN(num)) sum += num;
    }
    return sum;
  } catch {
    return 0;
  }
}

async function sumFilteredColumn({
  year,
  empresaIds,
  whereSql,
}: {
  year: number;
  empresaIds?: string[] | null;
  whereSql: ReturnType<typeof sql>;
}): Promise<number> {
  let query = sql`
    SELECT t.arrecadado AS val
    FROM fct_receitas t
    WHERE t.ano = ${year}
      AND (${whereSql})
  `;

  if (empresaIds && empresaIds.length > 0) {
    query = sql`${query} AND t.empresa_id = ANY(${empresaIds})`;
  }

  try {
    const res = await query.execute(db);
    if (!res.rows || res.rows.length === 0) return 0;
    let sum = 0;
    for (const row of res.rows as { val?: unknown }[]) {
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
    const [
      totalPrevisto,
      totalArrecadado,
      uniaoPrevisto,
      uniaoArrecadado,
      estadoPrevisto,
      estadoArrecadado,
      propriaDirectPrevisto,
      propriaDirectArrecadado,
      emendasPixArrecadado,
      emendasIndividuaisArrecadado,
      fpmArrecadado,
      icmsArrecadado,
      issIptuArrecadado,
    ] = await Promise.all([
      sumColumn({
        tipoReceita: "orcamentaria",
        col: "previsao_atualizada",
        year,
        rootOnly: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "orcamentaria",
        col: "arrecadado",
        year,
        rootOnly: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "uniao",
        col: "previsao_atualizada",
        year,
        rootOnly: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "uniao",
        col: "arrecadado",
        year,
        rootOnly: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "estado",
        col: "previsao_atualizada",
        year,
        rootOnly: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "estado",
        col: "arrecadado",
        year,
        rootOnly: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "orcamentaria",
        col: "previsao_atualizada",
        year,
        rootOnly: true,
        notTransfer: true,
        empresaIds,
      }),
      sumColumn({
        tipoReceita: "orcamentaria",
        col: "arrecadado",
        year,
        rootOnly: true,
        notTransfer: true,
        empresaIds,
      }),
      sumFilteredColumn({
        year,
        empresaIds,
        whereSql: sql`t.tipo_receita IN ('uniao', 'estado', 'orcamentaria') AND (t.descricao ILIKE '%TRANSFERENCIA ESPECIAL%' OR t.codigo LIKE '1.7.1.5%')`,
      }),
      sumFilteredColumn({
        year,
        empresaIds,
        whereSql: sql`t.tipo_receita IN ('uniao', 'estado', 'orcamentaria') AND (t.descricao ILIKE '%EMENDA%' OR t.descricao ILIKE '%PARLAMENTAR%') AND NOT (t.descricao ILIKE '%TRANSFERENCIA ESPECIAL%' OR t.codigo LIKE '1.7.1.5%')`,
      }),
      sumFilteredColumn({
        year,
        empresaIds,
        whereSql: sql`t.codigo LIKE '1.7.1.8.01.2%' OR t.descricao ILIKE '%FUNDO DE PARTICIPACAO%'`,
      }),
      sumFilteredColumn({
        year,
        empresaIds,
        whereSql: sql`t.codigo LIKE '1.7.2.8.01.1%' OR t.descricao ILIKE '%ICMS%'`,
      }),
      sumFilteredColumn({
        year,
        empresaIds,
        whereSql: sql`t.codigo LIKE '1.1.1.8.01%' OR t.codigo LIKE '1.1.1.8.02%' OR t.descricao ILIKE '%IPTU%' OR t.descricao ILIKE '%ISS%'`,
      }),
    ]);

    const emendasTotalArrecadado =
      emendasPixArrecadado + emendasIndividuaisArrecadado;

    const propriaPrevisto =
      propriaDirectPrevisto > 0
        ? propriaDirectPrevisto
        : Math.max(0, totalPrevisto - uniaoPrevisto - estadoPrevisto);

    const propriaArrecadado =
      propriaDirectArrecadado > 0
        ? propriaDirectArrecadado
        : Math.max(0, totalArrecadado - uniaoArrecadado - estadoArrecadado);

    const pctPrevisto =
      totalPrevisto > 0 ? (propriaPrevisto / totalPrevisto) * 100 : 0;
    const pct =
      totalArrecadado > 0
        ? (propriaArrecadado / totalArrecadado) * 100
        : pctPrevisto;

    records.push({
      ano: year,
      receitaPropria: propriaArrecadado,
      transferenciasUniao: uniaoArrecadado,
      transferenciasEstado: estadoArrecadado,
      total: totalArrecadado,
      pctPropria: pct,
      pctPropriaPrevisto: pctPrevisto,
      alertaDependencia: pct < 10,
      receitaPropriaPrevisto: propriaPrevisto,
      receitaPropriaArrecadado: propriaArrecadado,
      transferenciasUniaoPrevisto: uniaoPrevisto,
      transferenciasUniaoArrecadado: uniaoArrecadado,
      transferenciasEstadoPrevisto: estadoPrevisto,
      transferenciasEstadoArrecadado: estadoArrecadado,
      totalPrevisto,
      totalArrecadado,
      pctArrecadado: totalPrevisto > 0 ? totalArrecadado / totalPrevisto : 0,
      emendasTotalArrecadado,
      emendasPixArrecadado,
      emendasIndividuaisArrecadado,
      fpmArrecadado,
      icmsArrecadado,
      issIptuArrecadado,
    });
  }

  for (let i = 0; i < records.length; i++) {
    if (i === 0) {
      records[i].totalPctChange = null;
    } else {
      const prevTotal = records[i - 1].total;
      records[i].totalPctChange =
        prevTotal > 0
          ? ((records[i].total - prevTotal) / prevTotal) * 100
          : null;
    }
  }

  return records;
}
