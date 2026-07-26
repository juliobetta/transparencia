import { sql } from "kysely";
import { db } from "../client";
import { getFontesReceita } from "./fontes_receita";

export interface RestoPendente {
  ano: number;
  administracao: "Adm. Anterior" | "Adm. Atual";
  empenhado: number;
  pago: number;
  pendente: number;
}

export interface TopCredor {
  Fornecedor: string;
  Pendente: number;
}

export interface PosicaoFiscalResult {
  totalArrecadado: number;
  despesasPagas: number;
  restosPagosNoAno: number;
  totalSaidas: number;
  saldoEstimado: number;
  saldoAposRestos: number;
  restosPendentes: RestoPendente[];
  restosPendentesTotal: number;
  restosPendentesAnteriores: number;
  topCredoresAdmAtual: TopCredor[];
  totalCredoresAdmAtual: number;
}

export interface FornecedorPendente {
  descricao: string;
  aguardandoDesde: number;
  numRegistros: number;
  totalEmpenhado: number;
  totalPago: number;
  pendente: number;
}

export interface RestoBaixoValor {
  Ano: number;
  Nº: string;
  Descrição: string;
  Empenhado: number;
  Pago: number;
}

function sanitizeDescricao(s: string): string {
  if (!s) return "Sem identificação";
  return s.trim().replace(/^\d{2}\.\d{3}\.\d{3}\s+/, "");
}

async function sumVarcharCol({
  table,
  col,
  year,
  whereExtra = "",
  empresaIds,
}: {
  table: string;
  col: string;
  year: number;
  whereExtra?: string;
  empresaIds?: string[] | null;
}): Promise<number> {
  try {
    let query = sql`SELECT ${sql.ref(col)} AS val FROM ${sql.raw(table)} WHERE ano = ${year} ${sql.raw(whereExtra)}`;
    if (empresaIds && empresaIds.length > 0) {
      if (table === "fct_despesas_por_orgao") {
        query = sql`${query} AND empresa = ANY(${empresaIds})`;
      } else {
        query = sql`${query} AND empresa_id = ANY(${empresaIds})`;
      }
    }
    const res = await query.execute(db);
    if (!res.rows) return 0;
    let sum = 0;
    for (const r of res.rows as any[]) {
      const num = parseFloat(String(r.val ?? "0").replace(",", "."));
      if (!Number.isNaN(num)) sum += num;
    }
    return sum;
  } catch {
    return 0;
  }
}

export async function getPosicaoFiscal(
  year: number,
  empresaIds?: string[] | null,
): Promise<PosicaoFiscalResult> {
  const revDf = await getFontesReceita([year], empresaIds);
  const totalArrecadado = revDf.length > 0 ? revDf[0].totalArrecadado : 0;

  const despesasPagas = await sumVarcharCol({
    table: "fct_despesas_por_orgao",
    col: "pago",
    year,
    empresaIds,
  });
  const restosPagosNoAno = await sumVarcharCol({
    table: "fct_despesas",
    col: "pago",
    year,
    whereExtra: "AND fonte = 'restos_a_pagar'",
    empresaIds,
  });

  const restosPendentes: RestoPendente[] = [];
  try {
    let q = sql`SELECT ano, empenhado, pago FROM fct_despesas WHERE fonte = 'restos_a_pagar' AND ano <= ${year}`;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    q = sql`${q} ORDER BY ano`;

    const res = await q.execute(db);
    const byYear: Record<number, { empenhado: number; pago: number }> = {};

    for (const row of (res.rows as any[]) || []) {
      const a = Number(row.ano);
      const emp =
        parseFloat(String(row.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(row.pago ?? "0").replace(",", ".")) || 0;

      if (!byYear[a]) byYear[a] = { empenhado: 0, pago: 0 };
      byYear[a].empenhado += emp;
      byYear[a].pago += pag;
    }

    const sortedYears = Object.keys(byYear)
      .map(Number)
      .sort((a, b) => a - b);
    for (const a of sortedYears) {
      const emp = byYear[a].empenhado;
      const pag = byYear[a].pago;
      restosPendentes.push({
        ano: a,
        administracao: a < year ? "Adm. Anterior" : "Adm. Atual",
        empenhado: emp,
        pago: pag,
        pendente: emp - pag,
      });
    }
  } catch {}

  const totalSaidas = despesasPagas + restosPagosNoAno;
  const saldoEstimado = totalArrecadado - totalSaidas;
  const restosPendentesTotal = restosPendentes.reduce(
    (acc, r) => acc + r.pendente,
    0,
  );
  const restosPendentesAnteriores = restosPendentes
    .filter((r) => r.ano < year)
    .reduce((acc, r) => acc + r.pendente, 0);

  let credoresAdmAtual: TopCredor[] = [];
  try {
    let qCred = sql`SELECT descricao, empenhado, pago FROM fct_despesas WHERE fonte = 'restos_a_pagar' AND ano <= ${year}`;
    if (empresaIds && empresaIds.length > 0) {
      qCred = sql`${qCred} AND empresa_id = ANY(${empresaIds})`;
    }
    const resCred = await qCred.execute(db);
    const byDesc: Record<string, number> = {};

    for (const r of (resCred.rows as any[]) || []) {
      const desc = sanitizeDescricao(r.descricao);
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const pend = emp - pag;

      if (pend > 0) {
        byDesc[desc] = (byDesc[desc] || 0) + pend;
      }
    }

    credoresAdmAtual = Object.entries(byDesc)
      .map(([Fornecedor, Pendente]) => ({ Fornecedor, Pendente }))
      .sort((a, b) => b.Pendente - a.Pendente);
  } catch {}

  return {
    totalArrecadado,
    despesasPagas,
    restosPagosNoAno,
    totalSaidas,
    saldoEstimado,
    saldoAposRestos: saldoEstimado - restosPendentesTotal,
    restosPendentes,
    restosPendentesTotal,
    restosPendentesAnteriores,
    topCredoresAdmAtual: credoresAdmAtual.slice(0, 5),
    totalCredoresAdmAtual: credoresAdmAtual.length,
  };
}

export async function getFornecedoresPendentes(
  year?: number | null,
  empresaIds?: string[] | null,
): Promise<FornecedorPendente[]> {
  try {
    let q = sql`SELECT descricao, ano, empenhado, pago FROM fct_despesas WHERE fonte = 'restos_a_pagar'`;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const map: Record<
      string,
      {
        minAno: number;
        count: number;
        totalEmp: number;
        totalPago: number;
        pendente: number;
      }
    > = {};

    for (const r of (res.rows as any[]) || []) {
      const a = Number(r.ano);
      if (year !== undefined && year !== null && a > year) continue;

      const desc = sanitizeDescricao(r.descricao);
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const pend = emp - pag;

      if (!map[desc]) {
        map[desc] = {
          minAno: a,
          count: 0,
          totalEmp: 0,
          totalPago: 0,
          pendente: 0,
        };
      }
      map[desc].count += 1;
      map[desc].minAno = Math.min(map[desc].minAno, a);
      map[desc].totalEmp += emp;
      map[desc].totalPago += pag;
      map[desc].pendente += pend;
    }

    return Object.entries(map)
      .filter(([_, v]) => v.pendente > 0)
      .map(([descricao, v]) => ({
        descricao,
        aguardandoDesde: v.minAno,
        numRegistros: v.count,
        totalEmpenhado: v.totalEmp,
        totalPago: v.totalPago,
        pendente: v.pendente,
      }))
      .sort((a, b) => b.pendente - a.pendente);
  } catch {
    return [];
  }
}

export async function getRestosBaixoValor(
  year?: number | null,
  threshold: number = 10.0,
  empresaIds?: string[] | null,
): Promise<RestoBaixoValor[]> {
  try {
    let q = sql`SELECT descricao, ano, empenho_id, empenhado, pago FROM fct_despesas WHERE fonte = 'restos_a_pagar'`;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const list: RestoBaixoValor[] = [];

    for (const r of (res.rows as any[]) || []) {
      const a = Number(r.ano);
      if (year !== undefined && year !== null && a > year) continue;

      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;

      if (emp > 0 && emp < threshold) {
        list.push({
          Ano: a,
          Nº: String(r.empenho_id ?? ""),
          Descrição: sanitizeDescricao(r.descricao),
          Empenhado: emp,
          Pago: pag,
        });
      }
    }

    return list.sort((a, b) => a.Empenhado - b.Empenhado);
  } catch {
    return [];
  }
}
