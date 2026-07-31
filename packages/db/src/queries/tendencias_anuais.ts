import { sql } from "kysely";
import { db } from "../client";
import { getFontesReceita } from "./fontes_receita";

export interface TendenciaAnualRecord {
  ano: number;
  totalGasto: number;
  totalEmpenhado: number;
  totalFolha: number;
  totalReceita: number | null;
  restosAPagar: number;
  totalGastoPctChange?: number | null;
  totalEmpenhadoPctChange?: number | null;
  totalFolhaPctChange?: number | null;
  totalReceitaPctChange?: number | null;
  restosAPagarPctChange?: number | null;
}

export async function getTendenciasAnuais(
  years: number[],
  empresaIds?: string[] | null,
  portalSlug: string = "porciuncula_prefeitura",
): Promise<TendenciaAnualRecord[]> {
  const sortedYears = [...years].sort((a, b) => a - b);
  const revDf = await getFontesReceita(sortedYears, empresaIds);
  const revMap = new Map<number, number>();
  for (const r of revDf) {
    revMap.set(r.ano, r.totalArrecadado);
  }

  const records: TendenciaAnualRecord[] = [];

  for (const year of sortedYears) {
    let totalGasto = 0;
    let totalEmpenhado = 0;
    try {
      let q = sql`SELECT pago, empenhado FROM fct_despesas_por_orgao WHERE ano = ${year}`;
      if (empresaIds && empresaIds.length > 0) {
        q = sql`${q} AND empresa = ANY(${empresaIds})`;
      }
      const res = await q.execute(db);
      for (const r of (res.rows as any[]) || []) {
        totalGasto += parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
        totalEmpenhado +=
          parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    let totalFolha = 0;
    try {
      const resF =
        await sql`SELECT proventos FROM fct_pessoal WHERE ano = ${year} AND portal_slug = ${portalSlug}`.execute(
          db,
        );
      for (const r of (resF.rows as any[]) || []) {
        totalFolha +=
          parseFloat(String(r.proventos ?? "0").replace(",", ".")) || 0;
      }
    } catch {}

    const totalRec = revMap.get(year) || 0;
    const receita = totalRec > 0 ? totalRec : null;

    let restos = 0;
    try {
      let qR = sql`SELECT pago FROM fct_despesas WHERE ano = ${year} AND fonte = 'restos_a_pagar' AND portal_slug = ${portalSlug}`;
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
      totalGasto,
      totalEmpenhado,
      totalFolha,
      totalReceita: receita,
      restosAPagar: restos,
    });
  }

  for (let i = 0; i < records.length; i++) {
    if (i === 0) {
      records[i].totalGastoPctChange = null;
      records[i].totalEmpenhadoPctChange = null;
      records[i].totalFolhaPctChange = null;
      records[i].totalReceitaPctChange = null;
      records[i].restosAPagarPctChange = null;
    } else {
      const prev = records[i - 1];
      const curr = records[i];

      curr.totalGastoPctChange =
        prev.totalGasto > 0
          ? ((curr.totalGasto - prev.totalGasto) / prev.totalGasto) * 100
          : null;
      curr.totalEmpenhadoPctChange =
        prev.totalEmpenhado > 0
          ? ((curr.totalEmpenhado - prev.totalEmpenhado) /
              prev.totalEmpenhado) *
            100
          : null;
      curr.totalFolhaPctChange =
        prev.totalFolha > 0
          ? ((curr.totalFolha - prev.totalFolha) / prev.totalFolha) * 100
          : null;
      curr.totalReceitaPctChange =
        prev.totalReceita && prev.totalReceita > 0 && curr.totalReceita
          ? ((curr.totalReceita - prev.totalReceita) / prev.totalReceita) * 100
          : null;
      curr.restosAPagarPctChange =
        prev.restosAPagar > 0
          ? ((curr.restosAPagar - prev.restosAPagar) / prev.restosAPagar) * 100
          : null;
    }
  }

  return records;
}
