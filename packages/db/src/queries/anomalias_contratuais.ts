import { sql } from "kysely";
import { db } from "../client";
import { dispensationThreshold, NEAR_THRESHOLD_PCT } from "../constants";

export interface ContratoFracionamento {
  ano: number;
  empresa: string;
  numero: string;
  fornecedor: string;
  objeto: string;
  valor_contrato: number;
  licitacao_numero: string;
  mes: number;
  Periodo: string;
}

export interface FornecedorRecorrente {
  empresa: string;
  fornecedor: string;
  quantidade: number;
  total: number;
  pct: number;
}

export interface AnomaliasResult {
  fracionamento: ContratoFracionamento[];
  fornecedor_recorrente: FornecedorRecorrente[];
  janela_curta: any[];
}

export async function contagensFracionamentoPorAno(
  years: number[],
  empresaIds?: string[] | null,
): Promise<Record<number, number>> {
  const result: Record<number, number> = {};
  for (const y of years) result[y] = 0;

  try {
    let q = sql`
      SELECT ano, empresa_id AS empresa, fornecedor_nome AS fornecedor, valor_contrato, numero_obra, tipo_obra, objeto
      FROM fct_contratos
      WHERE ano = ANY(${years})
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    for (const y of years) {
      const proximoMap: Record<string, number> = {};
      const yearRows = rows.filter((r) => Number(r.ano) === y);

      for (const r of yearRows) {
        const val =
          parseFloat(String(r.valor_contrato ?? "0").replace(",", ".")) || 0;
        const lim = dispensationThreshold(r.numero_obra, r.tipo_obra, r.objeto);
        const limInf = lim * (1 - NEAR_THRESHOLD_PCT);

        if (val >= limInf && val < lim) {
          const key = `${r.empresa ?? ""}__${r.fornecedor ?? ""}`;
          proximoMap[key] = (proximoMap[key] || 0) + 1;
        }
      }

      const countOver3 = Object.values(proximoMap).filter((c) => c >= 3).length;
      result[y] = countOver3;
    }
  } catch {}

  return result;
}

export async function getAnomaliasContratuais(
  year: number,
  empresaIds?: string[] | null,
): Promise<AnomaliasResult> {
  const fracionamento: ContratoFracionamento[] = [];
  const fornecedor_recorrente: FornecedorRecorrente[] = [];
  const janela_curta: any[] = [];

  try {
    let q = sql`
      SELECT ano, empresa_id AS empresa, contrato_numero AS numero, fornecedor_nome AS fornecedor, objeto, valor_contrato, licitacao_numero, mes, numero_obra, tipo_obra, modalidade, fundlegal
      FROM fct_contratos
      WHERE ano = ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const contratos = (res.rows as any[]) || [];

    const proximo: any[] = [];
    const empresaTotalCount: Record<string, number> = {};
    const empresaFornecedorCount: Record<string, Record<string, number>> = {};

    for (const c of contratos) {
      const emp = String(c.empresa ?? "");
      const forn = String(c.fornecedor ?? "");
      const val =
        parseFloat(String(c.valor_contrato ?? "0").replace(",", ".")) || 0;
      const lim = dispensationThreshold(c.numero_obra, c.tipo_obra, c.objeto);
      const limInf = lim * (1 - NEAR_THRESHOLD_PCT);

      empresaTotalCount[emp] = (empresaTotalCount[emp] || 0) + 1;
      if (!empresaFornecedorCount[emp]) empresaFornecedorCount[emp] = {};
      empresaFornecedorCount[emp][forn] =
        (empresaFornecedorCount[emp][forn] || 0) + 1;

      if (val >= limInf && val < lim) {
        proximo.push({ ...c, valor_num: val });
      }
    }

    const countFrac: Record<string, number> = {};
    for (const p of proximo) {
      const key = `${p.empresa ?? ""}__${p.fornecedor ?? ""}`;
      countFrac[key] = (countFrac[key] || 0) + 1;
    }

    const chavesFrac = new Set(
      Object.entries(countFrac)
        .filter(([_, cnt]) => cnt >= 3)
        .map(([k, _]) => k),
    );

    for (const p of proximo) {
      const key = `${p.empresa ?? ""}__${p.fornecedor ?? ""}`;
      if (chavesFrac.has(key)) {
        const mStr = String(p.mes ?? "").padStart(2, "0");
        fracionamento.push({
          ano: Number(p.ano),
          empresa: String(p.empresa ?? ""),
          numero: String(p.numero ?? ""),
          fornecedor: String(p.fornecedor ?? ""),
          objeto: String(p.objeto ?? ""),
          valor_contrato: p.valor_num,
          licitacao_numero: String(p.licitacao_numero ?? ""),
          mes: Number(p.mes),
          Periodo: `${mStr}/${p.ano}`,
        });
      }
    }

    for (const [emp, mapForn] of Object.entries(empresaFornecedorCount)) {
      const tot = empresaTotalCount[emp] || 0;
      if (tot === 0) continue;
      for (const [forn, qtd] of Object.entries(mapForn)) {
        const pct = qtd / tot;
        if (pct > 0.5) {
          fornecedor_recorrente.push({
            empresa: emp,
            fornecedor: forn,
            quantidade: qtd,
            total: tot,
            pct,
          });
        }
      }
    }
  } catch {}

  return {
    fracionamento,
    fornecedor_recorrente,
    janela_curta,
  };
}
