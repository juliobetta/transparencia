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
  historico_local_pago: number;
  historico_externo_pago: number;
  historico_total_pago: number;
  historico_pct_local: number;
}

export interface FornecedorRestosPendente {
  fornecedor: string;
  valor: number;
}

export interface RestosAPagarResumo {
  total_pendente: number;
  fornecedores_aguardando: number;
  divida_mais_antiga_ano: number;
  top_fornecedores: FornecedorRestosPendente[];
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

const FORNECEDORES_NATUREZA_MAP = [
  "30", // Material de Consumo",
  "36", // Serv. Terceiros (Pessoa Física)",
  "39", // Serv. Terceiros (Pessoa Jurídica)",
  "52", // Equipamentos e Mat. Permanente",
];

const _ELEMENTOS_COMPRAS_SERVICOS_INVESTIMENTOS = [
  ...FORNECEDORES_NATUREZA_MAP,
  "31",
  "32",
  "33",
  "35",
  "37",
  "40",
  "51",
];

export async function getImpactoGastosLocais({
  year,
  empresaIds,
  cidadeClean,
  portalSlug,
}: {
  year: number;
  empresaIds?: string[] | null;
  /** Nome da cidade limpa (sem acentos e em caixa alta) */
  cidadeClean: string;
  portalSlug: string;
}): Promise<ImpactoGastosLocais> {
  try {
    // 1. Query para o ano selecionado
    let qYear = sql`
      SELECT DISTINCT
        f.codigo,
        f.descricao,
        f.fornecedor_cidade,
        f.fornecedor_cidade_clean,
        f.pago,
        f.empenhado
      FROM fct_despesas_por_fornecedor f
      LEFT JOIN fct_despesas g
        ON f.ano = g.ano
        AND f.descricao = g.fornecedor_nome
      WHERE f.ano = ${year}
        AND g.elemento = ANY(${FORNECEDORES_NATUREZA_MAP})
        AND g.portal_slug = ${portalSlug}
    `;
    if (empresaIds && empresaIds.length > 0) {
      qYear = sql`${qYear} AND f.empresa = ANY(${empresaIds})`;
    }
    const resYear = await qYear.execute(db);
    const rowsYear = (resYear.rows as any[]) || [];

    let local_pago = 0;
    let externo_pago = 0;

    for (const r of rowsYear) {
      const p = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const rawCid = String(
        r.fornecedor_cidade_clean || r.fornecedor_cidade || "",
      )
        .trim()
        .toUpperCase();
      const cid = rawCid.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      if (cid === cidadeClean) {
        local_pago += p;
      } else {
        externo_pago += p;
      }
    }

    const total_pago = local_pago + externo_pago;
    const pct_local = total_pago > 0 ? (local_pago / total_pago) * 100 : 0;

    // 2. Query plurianual acumulada (todos os anos)
    let qHist = sql`
      SELECT DISTINCT
        f.codigo,
        f.descricao,
        f.fornecedor_cidade,
        f.fornecedor_cidade_clean,
        f.pago
      FROM fct_despesas_por_fornecedor f
      LEFT JOIN fct_despesas g
        ON f.ano = g.ano
        AND f.descricao = g.fornecedor_nome
      WHERE g.elemento = ANY(${FORNECEDORES_NATUREZA_MAP}) and f.ano < ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      qHist = sql`${qHist} AND f.empresa = ANY(${empresaIds})`;
    }
    const resHist = await qHist.execute(db);
    const rowsHist = (resHist.rows as any[]) || [];

    let historico_local_pago = 0;
    let historico_externo_pago = 0;

    for (const r of rowsHist) {
      const p = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const rawCid = String(
        r.fornecedor_cidade_clean || r.fornecedor_cidade || "",
      )
        .trim()
        .toUpperCase();
      const cid = rawCid.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      if (cid === cidadeClean) {
        historico_local_pago += p;
      } else {
        historico_externo_pago += p;
      }
    }

    const historico_total_pago = historico_local_pago + historico_externo_pago;
    const historico_pct_local =
      historico_total_pago > 0
        ? (historico_local_pago / historico_total_pago) * 100
        : 0;

    return {
      local_pago,
      externo_pago,
      total_pago,
      pct_local,
      historico_local_pago,
      historico_externo_pago,
      historico_total_pago,
      historico_pct_local,
    };
  } catch {
    return {
      local_pago: 0,
      externo_pago: 0,
      total_pago: 0,
      pct_local: 0,
      historico_local_pago: 0,
      historico_externo_pago: 0,
      historico_total_pago: 0,
      historico_pct_local: 0,
    };
  }
}

export async function getRestosAPagarResumo(
  year: number,
  empresaIds?: string[] | null,
): Promise<RestosAPagarResumo> {
  try {
    let q = sql`
      SELECT
        ano,
        descricao,
        fornecedor_nome,
        empenhado,
        pago
      FROM fct_despesas
      WHERE fonte = 'restos_a_pagar'
        AND ano <= ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    let total_pendente = 0;
    const fornecedoresSet = new Set<string>();
    let divida_mais_antiga_ano = year;
    const mapFornecedores: Record<string, number> = {};

    for (const r of rows) {
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const pend = emp - pag;
      if (pend > 0) {
        const a = Number(r.ano);
        if (a > 0 && a < divida_mais_antiga_ano) {
          divida_mais_antiga_ano = a;
        }
        total_pendente += pend;
        const nome = String(
          r.fornecedor_nome || r.descricao || "Não identificado",
        ).trim();
        fornecedoresSet.add(nome);
        mapFornecedores[nome] = (mapFornecedores[nome] || 0) + pend;
      }
    }

    const top_fornecedores = Object.entries(mapFornecedores)
      .map(([fornecedor, valor]) => ({ fornecedor, valor }))
      .sort((a, b) => b.valor - a.valor)
      .slice(0, 5);

    return {
      total_pendente,
      fornecedores_aguardando: fornecedoresSet.size,
      divida_mais_antiga_ano,
      top_fornecedores,
    };
  } catch {
    return {
      total_pendente: 0,
      fornecedores_aguardando: 0,
      divida_mais_antiga_ano: year,
      top_fornecedores: [],
    };
  }
}
