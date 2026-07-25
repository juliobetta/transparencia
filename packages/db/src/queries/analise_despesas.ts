import { sql } from "kysely";
import { db } from "../client";

export interface MetricasDespesas {
  empenhado: number;
  liquidado: number;
  pago: number;
  taxa_liquidacao: number;
  taxa_pagamento: number;
}

export interface DespesaUnidade {
  descricao: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  dotacao_atualizada: number;
}

export interface FornecedorDetalhado {
  fornecedor: string;
  insmf: string;
  cidade: string;
  codigo: string;
  elemento: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  descricao: string;
}

export interface ImpactoGastosLocais {
  local_pago: number;
  externo_pago: number;
  total_pago: number;
  pct_local: number;
}

export interface ResumoDiarias {
  total_valor: number;
  total_viajantes: number;
  media_reembolso: number;
}

export interface TransacaoPesquisavel {
  data: string;
  fornecedor: string;
  pago: number;
  unidade: string;
  descricao: string;
}

export interface DiariaPesquisavel {
  data: string;
  servidor: string;
  cargo: string;
  valor: number;
  unidade: string;
  historico: string;
}

export interface ComposicaoDespesa {
  categoria: string;
  pago: number;
}

async function sumColWhere(
  table: string,
  col: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<number> {
  try {
    let q = sql`SELECT ${sql.ref(col)} AS val FROM ${sql.raw(table)} WHERE ano = ${year}`;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    let sum = 0;
    for (const r of (res.rows as any[]) || []) {
      const num = parseFloat(String(r.val ?? "0").replace(",", ".")) || 0;
      sum += num;
    }
    return sum;
  } catch {
    return 0;
  }
}

export async function getMetricasGeraisDespesas(
  year: number,
  empresaIds?: string[] | null,
): Promise<MetricasDespesas> {
  const empenhado = await sumColWhere(
    "fct_despesas_por_unidade",
    "empenhado",
    year,
    empresaIds,
  );
  const liquidado = await sumColWhere(
    "fct_despesas_por_unidade",
    "liquidado",
    year,
    empresaIds,
  );
  const pago = await sumColWhere(
    "fct_despesas_por_unidade",
    "pago",
    year,
    empresaIds,
  );

  return {
    empenhado,
    liquidado,
    pago,
    taxa_liquidacao: empenhado > 0 ? (liquidado / empenhado) * 100 : 0,
    taxa_pagamento: empenhado > 0 ? (pago / empenhado) * 100 : 0,
  };
}

export async function getDespesasPorUnidade(
  year: number,
  empresaIds?: string[] | null,
): Promise<DespesaUnidade[]> {
  try {
    let q = sql`
      SELECT codigo, descricao, empenhado, liquidado, pago, dotacao_atualizada
      FROM fct_despesas_por_unidade
      WHERE ano = ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const map: Record<
      string,
      {
        empenhado: number;
        liquidado: number;
        pago: number;
        dotacao_atualizada: number;
      }
    > = {};

    for (const r of (res.rows as any[]) || []) {
      const desc = String(r.descricao ?? "");
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const dot =
        parseFloat(String(r.dotacao_atualizada ?? "0").replace(",", ".")) || 0;

      if (!map[desc]) {
        map[desc] = {
          empenhado: 0,
          liquidado: 0,
          pago: 0,
          dotacao_atualizada: 0,
        };
      }
      map[desc].empenhado += emp;
      map[desc].liquidado += liq;
      map[desc].pago += pag;
      map[desc].dotacao_atualizada += dot;
    }

    return Object.entries(map)
      .map(([descricao, v]) => ({ descricao, ...v }))
      .sort((a, b) => b.pago - a.pago);
  } catch {
    return [];
  }
}

export async function getResumoDiarias(
  year: number,
  empresaIds?: string[] | null,
): Promise<ResumoDiarias> {
  try {
    let q = sql`SELECT valor, favorecido FROM fct_diarias WHERE ano = ${year}`;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];
    if (rows.length === 0)
      return { total_valor: 0, total_viajantes: 0, media_reembolso: 0 };

    let total_valor = 0;
    const viajantes = new Set<string>();

    for (const r of rows) {
      const v = parseFloat(String(r.valor ?? "0").replace(",", ".")) || 0;
      total_valor += v;
      if (r.favorecido) viajantes.add(String(r.favorecido));
    }

    const total_viajantes = viajantes.size;
    return {
      total_valor,
      total_viajantes,
      media_reembolso: rows.length > 0 ? total_valor / rows.length : 0,
    };
  } catch {
    return { total_valor: 0, total_viajantes: 0, media_reembolso: 0 };
  }
}

export async function getTransacoesPesquisaveis(
  year: number,
  queryStr: string = "",
  limit: number = 500,
  empresaIds?: string[] | null,
): Promise<TransacaoPesquisavel[]> {
  try {
    let q: ReturnType<typeof sql>;
    if (queryStr.trim()) {
      const search = `%${queryStr.trim()}%`;
      q = sql`
        SELECT f.data_empenho AS data, f.fornecedor_nome AS fornecedor, f.pago,
               COALESCE(d.orgao_nome, f.empresa_id) AS unidade, f.descricao
        FROM fct_despesas f
        LEFT JOIN dim_orgao d ON d.empresa_id = f.empresa_id
        WHERE f.ano = ${year}
          AND (f.fornecedor_nome ILIKE ${search} OR f.descricao ILIKE ${search}
               OR COALESCE(d.orgao_nome, f.empresa_id) ILIKE ${search})
      `;
      if (empresaIds && empresaIds.length > 0) {
        q = sql`${q} AND f.empresa_id = ANY(${empresaIds})`;
      }
      q = sql`${q} ORDER BY f.pago DESC LIMIT ${limit}`;
    } else {
      q = sql`
        SELECT f.data_empenho AS data, f.fornecedor_nome AS fornecedor, f.pago,
               COALESCE(d.orgao_nome, f.empresa_id) AS unidade, f.descricao
        FROM fct_despesas f
        LEFT JOIN dim_orgao d ON d.empresa_id = f.empresa_id
        WHERE f.ano = ${year}
      `;
      if (empresaIds && empresaIds.length > 0) {
        q = sql`${q} AND f.empresa_id = ANY(${empresaIds})`;
      }
      q = sql`${q} ORDER BY f.pago DESC LIMIT ${limit}`;
    }
    const res = await q.execute(db);
    return ((res.rows as any[]) || []).map((r) => ({
      data: String(r.data ?? ""),
      fornecedor: String(r.fornecedor ?? ""),
      pago: parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0,
      unidade: String(r.unidade ?? ""),
      descricao: String(r.descricao ?? ""),
    }));
  } catch {
    return [];
  }
}

export async function getComposicaoDespesa(
  year: number,
  empresaIds?: string[] | null,
): Promise<ComposicaoDespesa[]> {
  try {
    let q = sql`
      SELECT categoria, SUM(pago) AS pago FROM (
        SELECT
          CASE
            WHEN elemento IN ('01','03','11','13','16','91','92','93','94','96')
              THEN 'Pessoal e Encargos'
            WHEN elemento IN ('14')
              THEN 'Diárias'
            WHEN elemento IN ('30','31','32','33')
              THEN 'Material'
            WHEN elemento IN ('35','36','37','39')
              THEN 'Serviços de Terceiros'
            WHEN elemento IN ('41','42','43','46','47','48','70')
              THEN 'Transferências'
            WHEN elemento IN ('44','51','52','61','71')
              THEN 'Investimentos'
            ELSE 'Outros'
          END AS categoria,
          pago AS pago
        FROM fct_despesas
        WHERE ano = ${year} AND tipo_empenho != 'AN'
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    q = sql`${q}
      ) sub
      GROUP BY categoria
      ORDER BY pago DESC NULLS LAST
    `;
    const res = await q.execute(db);
    return ((res.rows as any[]) || [])
      .map((r) => ({
        categoria: String(r.categoria ?? ""),
        pago: parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0,
      }))
      .filter((i) => i.pago > 0);
  } catch {
    return [];
  }
}
