import { sql } from "kysely";
import { db } from "../client";
import { getFontesReceita } from "./fontes_receita";

export interface FolhaVsServicosRecord {
  ano: number;
  total_folha: number;
  total_pago: number;
  rcl_proxy: number;
  percentual_folha: number;
}

export interface DecimoTerceiroExecucao {
  empenhado: number;
  empenhado_bruto: number;
  liquidado: number;
  pago: number;
  pct_pago: number;
}

export async function getFolhaVsServicos(
  years: number[],
  empresaIds?: string[] | null,
): Promise<FolhaVsServicosRecord[]> {
  const records: FolhaVsServicosRecord[] = [];

  for (const year of years) {
    let total_folha = 0;
    try {
      const resF =
        await sql`SELECT proventos FROM fct_pessoal WHERE ano = ${year}`.execute(
          db,
        );
      for (const r of (resF.rows as any[]) || []) {
        total_folha +=
          parseFloat(String(r.proventos ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    let total_pago = 0;
    try {
      let qP = sql`SELECT pago FROM fct_despesas_por_orgao WHERE ano = ${year}`;
      if (empresaIds && empresaIds.length > 0) {
        qP = sql`${qP} AND empresa = ANY(${empresaIds})`;
      }
      const resP = await qP.execute(db);
      for (const r of (resP.rows as any[]) || []) {
        total_pago += parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    const revDf = await getFontesReceita([year], empresaIds);
    const rcl_proxy = revDf.length > 0 ? revDf[0].total : 0;
    const percentual_folha =
      rcl_proxy > 0 ? (total_folha / rcl_proxy) * 100 : 0;

    records.push({
      ano: year,
      total_folha,
      total_pago,
      rcl_proxy,
      percentual_folha,
    });
  }

  return records;
}

export async function getExecucaoDecimoTerceiro(
  year: number,
  empresaIds?: string[] | null,
): Promise<DecimoTerceiroExecucao | null> {
  try {
    let q = sql`
      SELECT
        SUM(CAST(REPLACE(empenhado, ',', '.') AS numeric)) as empenhado_bruto,
        SUM(CAST(REPLACE(empenhado_liquido, ',', '.') AS numeric)) as empenhado_liquido,
        SUM(CAST(REPLACE(liquidado, ',', '.') AS numeric)) as liquidado,
        SUM(CAST(REPLACE(pago, ',', '.') AS numeric)) as pago
      FROM fct_despesas
      WHERE ano = ${year}
        AND elemento IN ('01', '03', '11', '96')
        AND (descricao ILIKE '%13%' OR descricao ILIKE '%decimo terceiro%' OR descricao ILIKE '%décimo terceiro%')
        AND descricao NOT ILIKE '%anula%'
        AND descricao NOT ILIKE '%136%'
        AND descricao NOT ILIKE '%137%'
        AND descricao NOT ILIKE '%138%'
        AND descricao NOT ILIKE '%139%'
        AND tipo_empenho != 'AN'
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);

    const r = (res.rows as any[])?.[0];
    if (!r || r.empenhado_bruto === null || r.empenhado_bruto === undefined)
      return null;

    const emp_bruto = parseFloat(String(r.empenhado_bruto ?? "0")) || 0;
    const emp_liq = parseFloat(String(r.empenhado_liquido ?? "0")) || emp_bruto;
    const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
    const pag = parseFloat(String(r.pago ?? "0")) || 0;
    const pct_pago = emp_liq > 0 ? pag / emp_liq : 0;

    return {
      empenhado: emp_liq,
      empenhado_bruto: emp_bruto,
      liquidado: liq,
      pago: pag,
      pct_pago,
    };
  } catch {
    return null;
  }
}

export async function getPercentualChefiasEfetivas(
  year: number,
  _empresaIds?: string[] | null,
): Promise<number | null> {
  try {
    const res = await sql`
      SELECT
        COUNT(CASE WHEN (
          vinculo LIKE '%FG%' OR
          vinculo LIKE '%CC%' OR
          categoria_funcional = 'Efetivos ocupantes de cargo comissionado'
        ) THEN 1 END) AS efetivos_confianca,
        COUNT(CASE WHEN (
          categoria_funcional = 'Cargo comissionado extra-quadro' OR
          vinculo = 'Comissionado INSS' OR
          LOWER(vinculo) LIKE 'cargo comissionado%'
        ) THEN 1 END) AS comissionados_externos
      FROM fct_pessoal
      WHERE ano = ${year}
    `.execute(db);

    const row = (res.rows as any[])?.[0];
    const efetivosConfianca =
      parseFloat(String(row?.efetivos_confianca ?? "0")) || 0;
    const comissionadosExternos =
      parseFloat(String(row?.comissionados_externos ?? "0")) || 0;
    const totalConfianca = efetivosConfianca + comissionadosExternos;

    if (totalConfianca > 0) {
      return Number(((efetivosConfianca / totalConfianca) * 100).toFixed(1));
    }
  } catch {}
  return null;
}
