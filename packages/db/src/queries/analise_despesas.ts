import { sql } from "kysely";
import { db } from "../client";

export interface MetricasDespesas {
  empenhado: number;
  liquidado: number;
  pago: number;
  taxaLiquidacao: number;
  taxaPagamento: number;
}

export interface DespesaUnidade {
  descricao: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  dotacaoAtualizada: number;
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
  localPago: number;
  externoPago: number;
  totalPago: number;
  pctLocal: number;
  historicoLocalPago: number;
  historicoExternoPago: number;
  historicoTotalPago: number;
  historicoPctLocal: number;
}

export interface FornecedorRestosPendente {
  fornecedor: string;
  valor: number;
}

export interface RestosAPagarResumo {
  totalPendente: number;
  fornecedoresAguardando: number;
  dividaMaisAntigaAno: number;
  topFornecedores: FornecedorRestosPendente[];
}

export interface ResumoDiarias {
  totalValor: number;
  totalViajantes: number;
  mediaReembolso: number;
}

export interface BeneficiarioDiaria {
  favorecido: string;
  cargo: string | null;
  valor: number;
  viagens: number;
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

async function sumColWhere({
  table,
  col,
  year,
  empresaIds,
}: {
  table: string;
  col: string;
  year: number;
  empresaIds?: string[] | null;
}): Promise<number> {
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
  const empenhado = await sumColWhere({
    table: "fct_despesas_por_unidade",
    col: "empenhado",
    year,
    empresaIds,
  });
  const liquidado = await sumColWhere({
    table: "fct_despesas_por_unidade",
    col: "liquidado",
    year,
    empresaIds,
  });
  const pago = await sumColWhere({
    table: "fct_despesas_por_unidade",
    col: "pago",
    year,
    empresaIds,
  });

  return {
    empenhado,
    liquidado,
    pago,
    taxaLiquidacao: empenhado > 0 ? (liquidado / empenhado) * 100 : 0,
    taxaPagamento: empenhado > 0 ? (pago / empenhado) * 100 : 0,
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
        dotacaoAtualizada: number;
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
          dotacaoAtualizada: 0,
        };
      }
      map[desc].empenhado += emp;
      map[desc].liquidado += liq;
      map[desc].pago += pag;
      map[desc].dotacaoAtualizada += dot;
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
  portalSlug?: string | null,
): Promise<ResumoDiarias> {
  try {
    let q = sql`SELECT valor, favorecido FROM fct_diarias WHERE ano = ${year}`;
    if (portalSlug) {
      q = sql`${q} AND portal_slug = ${portalSlug}`;
    }
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];
    if (rows.length === 0)
      return { totalValor: 0, totalViajantes: 0, mediaReembolso: 0 };

    let totalValor = 0;
    const viajantes = new Set<string>();

    for (const r of rows) {
      const v = parseFloat(String(r.valor ?? "0").replace(",", ".")) || 0;
      totalValor += v;
      if (r.favorecido) viajantes.add(String(r.favorecido));
    }

    const totalViajantes = viajantes.size;
    return {
      totalValor,
      totalViajantes,
      mediaReembolso: rows.length > 0 ? totalValor / rows.length : 0,
    };
  } catch {
    return { totalValor: 0, totalViajantes: 0, mediaReembolso: 0 };
  }
}

export interface GetBeneficiariosDiariasParams {
  year: number;
  limit?: number;
  empresaIds?: string[] | null;
  portalSlug?: string | null;
}

export async function getPrincipaisBeneficiariosDiarias({
  year,
  limit = 10,
  empresaIds,
  portalSlug,
}: GetBeneficiariosDiariasParams): Promise<BeneficiarioDiaria[]> {
  try {
    let q = sql`
      SELECT favorecido, cargo, valor
      FROM fct_diarias
      WHERE ano = ${year}
    `;
    if (portalSlug) {
      q = sql`${q} AND portal_slug = ${portalSlug}`;
    }
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];
    if (rows.length === 0) return [];

    const map = new Map<
      string,
      {
        favorecido: string;
        cargo: string | null;
        valor: number;
        viagens: number;
      }
    >();

    for (const r of rows) {
      const fav = String(r.favorecido || "").trim();
      if (!fav) continue;
      const cargo = r.cargo ? String(r.cargo).trim() : null;
      const key = `${fav}||${cargo ?? ""}`;
      const v = parseFloat(String(r.valor ?? "0").replace(",", ".")) || 0;

      const existing = map.get(key);
      if (existing) {
        existing.valor += v;
        existing.viagens += 1;
      } else {
        map.set(key, { favorecido: fav, cargo, valor: v, viagens: 1 });
      }
    }

    return Array.from(map.values())
      .sort((a, b) => b.valor - a.valor)
      .slice(0, limit);
  } catch {
    return [];
  }
}

export interface GetTransacoesPesquisaveisParams {
  year: number;
  queryStr?: string;
  limit?: number;
  empresaIds?: string[] | null;
}

export async function getTransacoesPesquisaveis({
  year,
  queryStr = "",
  limit = 500,
  empresaIds,
}: GetTransacoesPesquisaveisParams): Promise<TransacaoPesquisavel[]> {
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

    let localPago = 0;
    let externoPago = 0;

    for (const r of rowsYear) {
      const p = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const rawCid = String(
        r.fornecedor_cidade_clean || r.fornecedor_cidade || "",
      )
        .trim()
        .toUpperCase();
      const cid = rawCid.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      if (cid === cidadeClean) {
        localPago += p;
      } else {
        externoPago += p;
      }
    }

    const totalPago = localPago + externoPago;
    const pctLocal = totalPago > 0 ? (localPago / totalPago) * 100 : 0;

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
      WHERE g.elemento = ANY(${FORNECEDORES_NATUREZA_MAP})
        AND f.ano < ${year}
        AND g.portal_slug = ${portalSlug}
    `;
    if (empresaIds && empresaIds.length > 0) {
      qHist = sql`${qHist} AND f.empresa = ANY(${empresaIds})`;
    }
    const resHist = await qHist.execute(db);
    const rowsHist = (resHist.rows as any[]) || [];

    let historicoLocalPago = 0;
    let historicoExternoPago = 0;

    for (const r of rowsHist) {
      const p = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const rawCid = String(
        r.fornecedor_cidade_clean || r.fornecedor_cidade || "",
      )
        .trim()
        .toUpperCase();
      const cid = rawCid.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      if (cid === cidadeClean) {
        historicoLocalPago += p;
      } else {
        historicoExternoPago += p;
      }
    }

    const historicoTotalPago = historicoLocalPago + historicoExternoPago;
    const historicoPctLocal =
      historicoTotalPago > 0
        ? (historicoLocalPago / historicoTotalPago) * 100
        : 0;

    return {
      localPago,
      externoPago,
      totalPago,
      pctLocal,
      historicoLocalPago,
      historicoExternoPago,
      historicoTotalPago,
      historicoPctLocal,
    };
  } catch {
    return {
      localPago: 0,
      externoPago: 0,
      totalPago: 0,
      pctLocal: 0,
      historicoLocalPago: 0,
      historicoExternoPago: 0,
      historicoTotalPago: 0,
      historicoPctLocal: 0,
    };
  }
}

export async function getRestosAPagarResumo(
  year: number,
  empresaIds?: string[] | null,
  portalSlug: string = "porciuncula_prefeitura",
): Promise<RestosAPagarResumo> {
  try {
    let q = sql`
      SELECT
        f.ano AS ano_exercicio,
        COALESCE(
          g.ano,
          (
            SELECT MIN(h.ano)
            FROM fct_despesas h
            WHERE h.empenho_id = f.empenho_id
              AND h.empresa_id = f.empresa_id
              AND h.fonte = 'restos_a_pagar'
              AND h.portal_slug = ${portalSlug}
          ),
          f.ano
        ) AS ano_origem,
        f.descricao,
        f.fornecedor_nome,
        f.empenhado,
        f.pago
      FROM fct_despesas f
      LEFT JOIN fct_despesas g
        ON f.empenho_id = g.empenho_id
       AND f.empresa_id = g.empresa_id
       AND g.fonte = 'exercicio'
       AND g.portal_slug = ${portalSlug}
      WHERE f.fonte = 'restos_a_pagar'
        AND f.ano = ${year}
        AND f.portal_slug = ${portalSlug}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND f.empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    let totalPendente = 0;
    const fornecedoresSet = new Set<string>();
    let dividaMaisAntigaAno = year;
    const mapFornecedores: Record<string, number> = {};

    for (const r of rows) {
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const pend = emp - pag;
      if (pend > 0) {
        const a = Number(r.ano_origem);
        if (a > 0 && a < dividaMaisAntigaAno) {
          dividaMaisAntigaAno = a;
        }
        totalPendente += pend;
        const nome = String(
          r.fornecedor_nome || r.descricao || "Não identificado",
        ).trim();
        fornecedoresSet.add(nome);
        mapFornecedores[nome] = (mapFornecedores[nome] || 0) + pend;
      }
    }

    const topFornecedores = Object.entries(mapFornecedores)
      .map(([fornecedor, valor]) => ({ fornecedor, valor }))
      .sort((a, b) => b.valor - a.valor)
      .slice(0, 5);

    return {
      totalPendente,
      fornecedoresAguardando: fornecedoresSet.size,
      dividaMaisAntigaAno,
      topFornecedores,
    };
  } catch {
    return {
      totalPendente: 0,
      fornecedoresAguardando: 0,
      dividaMaisAntigaAno: year,
      topFornecedores: [],
    };
  }
}
