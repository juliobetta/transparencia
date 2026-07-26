import { sql } from "kysely";
import { db } from "../client";
import { getFontesReceita } from "./fontes_receita";

export interface FolhaVsServicosRecord {
  ano: number;
  totalFolha: number;
  totalPago: number;
  rclProxy: number;
  percentualFolha: number;
}

export interface DecimoTerceiroExecucao {
  empenhado: number;
  empenhadoBruto: number;
  liquidado: number;
  pago: number;
  pctPago: number;
}

export async function getFolhaVsServicos(
  years: number[],
  empresaIds?: string[] | null,
): Promise<FolhaVsServicosRecord[]> {
  const records: FolhaVsServicosRecord[] = [];

  for (const year of years) {
    let totalFolha = 0;
    try {
      const resF =
        await sql`SELECT proventos FROM fct_pessoal WHERE ano = ${year}`.execute(
          db,
        );
      for (const r of (resF.rows as any[]) || []) {
        totalFolha +=
          parseFloat(String(r.proventos ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    let totalPago = 0;
    try {
      let qP = sql`SELECT pago FROM fct_despesas_por_orgao WHERE ano = ${year}`;
      if (empresaIds && empresaIds.length > 0) {
        qP = sql`${qP} AND empresa = ANY(${empresaIds})`;
      }
      const resP = await qP.execute(db);
      for (const r of (resP.rows as any[]) || []) {
        totalPago += parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    const revDf = await getFontesReceita([year], empresaIds);
    const rclProxy = revDf.length > 0 ? revDf[0].total : 0;
    const percentualFolha = rclProxy > 0 ? (totalFolha / rclProxy) * 100 : 0;

    records.push({
      ano: year,
      totalFolha,
      totalPago,
      rclProxy,
      percentualFolha,
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

    const empBruto = parseFloat(String(r.empenhado_bruto ?? "0")) || 0;
    const empLiq = parseFloat(String(r.empenhado_liquido ?? "0")) || empBruto;
    const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
    const pag = parseFloat(String(r.pago ?? "0")) || 0;
    const pctPago = empLiq > 0 ? pag / empLiq : 0;

    return {
      empenhado: empLiq,
      empenhadoBruto: empBruto,
      liquidado: liq,
      pago: pag,
      pctPago,
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
