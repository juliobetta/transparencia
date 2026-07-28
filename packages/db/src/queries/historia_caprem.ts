import { sql } from "kysely";
import { db } from "../client";

export const CAPREM_CODE = "1061";

export const ELEMENTO_LABELS: Record<string, string> = {
  "13": "Contribuições Patronais (RPPS/INSS)",
  "46": "Auxílio-Alimentação",
  "71": "Principal da Dívida Contratual Resgatado (Parcelamento)",
  "91": "Sentenças Judiciais",
  "97": "Aporte para Cobertura do Déficit Atuarial do RPPS",
};

export interface EntityCaprem {
  entidade: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  taxaExecucao: number;
}

export interface NaturezaCaprem {
  natureza: string;
  descricao: string;
  elemento: string;
  dataEmpenho?: string;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface MensalCaprem {
  mes: number;
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
  natureza: NaturezaCaprem[];
  mensal: MensalCaprem[];
  annualTrend: AnnualTrendCaprem[];
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  taxaExecucao: number;
  totalAporteAtuarial: number;
  totalDividaResgatada: number;
}

export async function getHistoriaCaprem(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<HistoriaCapremResult> {
  const entidades: EntityCaprem[] = [];
  const natureza: NaturezaCaprem[] = [];
  const mensal: MensalCaprem[] = [];
  let annualTrend: AnnualTrendCaprem[] = [];
  let totalEmpenhado = 0;
  let totalLiquidado = 0;
  let totalPago = 0;
  let totalAporteAtuarial = 0;
  let totalDividaResgatada = 0;

  try {
    let q = sql`
      SELECT o.orgao_nome AS entidade,
             SUM(CASE WHEN pg_typeof(f.empenhado)::text = 'numeric' THEN f.empenhado ELSE CAST(REPLACE(f.empenhado::text, ',', '.') AS numeric) END) AS empenhado,
             SUM(CASE WHEN pg_typeof(f.liquidado)::text = 'numeric' THEN f.liquidado ELSE CAST(REPLACE(f.liquidado::text, ',', '.') AS numeric) END) AS liquidado,
             SUM(CASE WHEN pg_typeof(f.pago)::text = 'numeric' THEN f.pago ELSE CAST(REPLACE(f.pago::text, ',', '.') AS numeric) END) AS pago
      FROM fct_despesas_por_fornecedor f
      JOIN dim_orgao o ON o.empresa_id = f.empresa::text AND o.portal_slug = ${portalSlug}
      WHERE (f.codigo = ${CAPREM_CODE} OR f.descricao ILIKE '%CAPREM%') AND f.ano = ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND f.empresa = ANY(${empresaIds})`;
    }
    q = sql`${q}
      GROUP BY o.orgao_nome
      ORDER BY empenhado DESC NULLS LAST
    `;
    const resE = await q.execute(db);

    for (const r of (resE.rows as Record<string, unknown>[]) || []) {
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      totalEmpenhado += emp;
      totalLiquidado += liq;
      totalPago += pag;
      entidades.push({
        entidade: String(r.entidade ?? ""),
        empenhado: emp,
        liquidado: liq,
        pago: pag,
        taxaExecucao: emp > 0 ? (pag / emp) * 100 : 0,
      });
    }
  } catch (err) {
    console.error("Error in getHistoriaCaprem entidades:", err);
  }

  try {
    let qN = sql`
      SELECT elemento,
             natureza_despesa AS natureza,
             MAX(data_empenho::text) AS data_empenho,
             SUM(CAST(empenhado AS numeric)) AS empenhado,
             SUM(CAST(liquidado AS numeric)) AS liquidado,
             SUM(CAST(pago AS numeric)) AS pago
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano = ${year}
        AND (fornecedor_nome ILIKE '%CAPREM%' OR elemento IN ('97', '71'))
        AND (tipo_empenho IS NULL OR tipo_empenho != 'AN')
    `;
    if (empresaIds && empresaIds.length > 0) {
      qN = sql`${qN} AND empresa_id = ANY(${empresaIds})`;
    }
    qN = sql`${qN}
      GROUP BY elemento, natureza_despesa
      ORDER BY empenhado DESC
    `;
    const resN = await qN.execute(db);

    for (const r of (resN.rows as Record<string, unknown>[]) || []) {
      const el = String(r.elemento ?? "");
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      const dtEmp = String(r.data_empenho ?? "");
      const natStr =
        ELEMENTO_LABELS[el] || String(r.natureza ?? "") || `Elemento ${el}`;

      natureza.push({
        natureza: natStr,
        descricao: natStr,
        elemento: el,
        dataEmpenho: dtEmp,
        empenhado: emp,
        liquidado: liq,
        pago: pag,
      });

      if (el === "97") {
        totalAporteAtuarial += emp;
      }
      if (el === "71") {
        totalDividaResgatada += emp;
      }
    }
  } catch (err) {
    console.error("Error in getHistoriaCaprem natureza:", err);
  }

  try {
    let qM = sql`
      SELECT mes,
             SUM(CAST(empenhado AS numeric)) AS empenhado,
             SUM(CAST(liquidado AS numeric)) AS liquidado,
             SUM(CAST(pago AS numeric)) AS pago
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano = ${year}
        AND (fornecedor_nome ILIKE '%CAPREM%' OR elemento IN ('97', '71'))
        AND (tipo_empenho IS NULL OR tipo_empenho != 'AN')
    `;
    if (empresaIds && empresaIds.length > 0) {
      qM = sql`${qM} AND empresa_id = ANY(${empresaIds})`;
    }
    qM = sql`${qM}
      GROUP BY mes
      ORDER BY mes
    `;
    const resM = await qM.execute(db);

    for (const r of (resM.rows as Record<string, unknown>[]) || []) {
      const m = Number(r.mes);
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      mensal.push({
        mes: m,
        empenhado: emp,
        liquidado: liq,
        pago: pag,
      });
    }
  } catch (err) {
    console.error("Error in getHistoriaCaprem mensal:", err);
  }

  try {
    const resA = await sql`
      SELECT f.ano,
             SUM(CASE WHEN pg_typeof(f.empenhado)::text = 'numeric' THEN f.empenhado ELSE CAST(REPLACE(f.empenhado::text, ',', '.') AS numeric) END) AS empenhado,
             SUM(CASE WHEN pg_typeof(f.liquidado)::text = 'numeric' THEN f.liquidado ELSE CAST(REPLACE(f.liquidado::text, ',', '.') AS numeric) END) AS liquidado,
             SUM(CASE WHEN pg_typeof(f.pago)::text = 'numeric' THEN f.pago ELSE CAST(REPLACE(f.pago::text, ',', '.') AS numeric) END) AS pago
      FROM fct_despesas_por_fornecedor f
      JOIN dim_orgao o ON o.empresa_id = f.empresa::text AND o.portal_slug = ${portalSlug}
      WHERE (f.codigo = ${CAPREM_CODE} OR f.descricao ILIKE '%CAPREM%')
      GROUP BY f.ano
      ORDER BY f.ano
    `.execute(db);

    annualTrend = ((resA.rows as Record<string, unknown>[]) || []).map((r) => ({
      ano: Number(r.ano),
      empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
      liquidado: parseFloat(String(r.liquidado ?? "0")) || 0,
      pago: parseFloat(String(r.pago ?? "0")) || 0,
    }));
  } catch (err) {
    console.error("Error in getHistoriaCaprem annualTrend:", err);
  }

  const taxaExecucao =
    totalEmpenhado > 0 ? totalPago / totalEmpenhado : 0;

  return {
    entidades,
    natureza,
    mensal,
    annualTrend,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    taxaExecucao,
    totalAporteAtuarial,
    totalDividaResgatada,
  };
}
