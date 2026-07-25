import { sql } from "kysely";
import { db } from "../client";
import { getFontesReceita } from "./fontes_receita";

export interface TendenciaAnualRecord {
  ano: number;
  total_gasto: number;
  total_empenhado: number;
  total_folha: number;
  total_receita: number | null;
  restos_a_pagar: number;
  total_gasto_pct_change?: number | null;
  total_empenhado_pct_change?: number | null;
  total_folha_pct_change?: number | null;
  total_receita_pct_change?: number | null;
  restos_a_pagar_pct_change?: number | null;
}

export async function getTendenciasAnuais(
  years: number[],
  empresaIds?: string[] | null,
): Promise<TendenciaAnualRecord[]> {
  const sortedYears = [...years].sort((a, b) => a - b);
  const revDf = await getFontesReceita(sortedYears, empresaIds);
  const revMap = new Map<number, number>();
  for (const r of revDf) {
    revMap.set(r.ano, r.total_arrecadado);
  }

  const records: TendenciaAnualRecord[] = [];

  for (const year of sortedYears) {
    let total_gasto = 0;
    let total_empenhado = 0;
    try {
      let q = sql`SELECT pago, empenhado FROM fct_despesas_por_orgao WHERE ano = ${year}`;
      if (empresaIds && empresaIds.length > 0) {
        q = sql`${q} AND empresa = ANY(${empresaIds})`;
      }
      const res = await q.execute(db);
      for (const r of (res.rows as any[]) || []) {
        total_gasto += parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
        total_empenhado +=
          parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

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

    const total_rec = revMap.get(year) || 0;
    const receita = total_rec > 0 ? total_rec : null;

    let restos = 0;
    try {
      let qR = sql`SELECT pago FROM fct_despesas WHERE ano = ${year} AND fonte = 'restos_a_pagar'`;
      if (empresaIds && empresaIds.length > 0) {
        qR = sql`${qR} AND empresa_id = ANY(${empresaIds})`;
      }
      const resR = await qR.execute(db);
      for (const r of (resR.rows as any[]) || []) {
        restos += parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    records.push({
      ano: year,
      total_gasto,
      total_empenhado,
      total_folha,
      total_receita: receita,
      restos_a_pagar: restos,
    });
  }

  for (let i = 0; i < records.length; i++) {
    if (i === 0) {
      records[i].total_gasto_pct_change = null;
      records[i].total_empenhado_pct_change = null;
      records[i].total_folha_pct_change = null;
      records[i].total_receita_pct_change = null;
      records[i].restos_a_pagar_pct_change = null;
    } else {
      const prev = records[i - 1];
      const curr = records[i];

      curr.total_gasto_pct_change =
        prev.total_gasto > 0
          ? ((curr.total_gasto - prev.total_gasto) / prev.total_gasto) * 100
          : null;
      curr.total_empenhado_pct_change =
        prev.total_empenhado > 0
          ? ((curr.total_empenhado - prev.total_empenhado) /
              prev.total_empenhado) *
            100
          : null;
      curr.total_folha_pct_change =
        prev.total_folha > 0
          ? ((curr.total_folha - prev.total_folha) / prev.total_folha) * 100
          : null;
      curr.total_receita_pct_change =
        prev.total_receita && prev.total_receita > 0 && curr.total_receita
          ? ((curr.total_receita - prev.total_receita) / prev.total_receita) *
            100
          : null;
      curr.restos_a_pagar_pct_change =
        prev.restos_a_pagar > 0
          ? ((curr.restos_a_pagar - prev.restos_a_pagar) /
              prev.restos_a_pagar) *
            100
          : null;
    }
  }

  return records;
}
