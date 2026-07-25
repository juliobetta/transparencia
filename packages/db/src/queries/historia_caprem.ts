import { sql } from "kysely";
import { db } from "../client";

export const CAPREM_CODE = "1061";

export interface EntityCaprem {
  entidade: string;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface AnnualTrendCaprem {
  ano: number;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface HistoriaCapremResult {
  entidades: EntityCaprem[];
  annual_trend: AnnualTrendCaprem[];
  total_empenhado: number;
  total_liquidado: number;
  total_pago: number;
}

export async function getHistoriaCaprem(
  year: number,
  empresaIds?: string[] | null,
): Promise<HistoriaCapremResult> {
  const entidades: EntityCaprem[] = [];
  let annual_trend: AnnualTrendCaprem[] = [];
  let total_empenhado = 0;
  let total_liquidado = 0;
  let total_pago = 0;

  try {
    let q = sql`
      SELECT o.orgao_nome AS entidade,
             SUM(CAST(REPLACE(f.empenhado, ',', '.') AS numeric)) AS empenhado,
             SUM(CAST(REPLACE(f.liquidado, ',', '.') AS numeric)) AS liquidado,
             SUM(CAST(REPLACE(f.pago, ',', '.') AS numeric)) AS pago
      FROM fct_despesas_por_fornecedor f
      JOIN dim_orgao o ON o.empresa_id = f.empresa::text
      WHERE f.codigo = ${CAPREM_CODE} AND f.ano = ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND f.empresa = ANY(${empresaIds})`;
    }
    q = sql`${q}
      GROUP BY o.orgao_nome
      ORDER BY empenhado DESC NULLS LAST
    `;
    const resE = await q.execute(db);

    for (const r of (resE.rows as any[]) || []) {
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      total_empenhado += emp;
      total_liquidado += liq;
      total_pago += pag;
      entidades.push({
        entidade: String(r.entidade ?? ""),
        empenhado: emp,
        liquidado: liq,
        pago: pag,
      });
    }
  } catch {}

  try {
    const resA = await sql`
      SELECT ano,
             SUM(CAST(REPLACE(empenhado, ',', '.') AS numeric)) AS empenhado,
             SUM(CAST(REPLACE(liquidado, ',', '.') AS numeric)) AS liquidado,
             SUM(CAST(REPLACE(pago, ',', '.') AS numeric)) AS pago
      FROM fct_despesas_por_fornecedor
      WHERE codigo = ${CAPREM_CODE}
      GROUP BY ano ORDER BY ano
    `.execute(db);

    annual_trend = ((resA.rows as any[]) || []).map((r) => ({
      ano: Number(r.ano),
      empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
      liquidado: parseFloat(String(r.liquidado ?? "0")) || 0,
      pago: parseFloat(String(r.pago ?? "0")) || 0,
    }));
  } catch {}

  return {
    entidades,
    annual_trend,
    total_empenhado,
    total_liquidado,
    total_pago,
  };
}
