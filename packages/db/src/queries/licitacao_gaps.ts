import { sql } from "kysely";
import { db } from "../client";
import { dispensationThreshold } from "../constants";

export const SAUDE_EMPRESA = "2";

export interface ContratoSemLicitacao {
  ano: number;
  empresa: string;
  numero: string;
  fornecedor: string;
  objeto: string;
  valor_contrato: string;
  licitacao_numero: string;
  mes: number;
  numero_obra: string | null;
  tipo_obra: string | null;
  modalidade: string | null;
  fundlegal: string | null;
  limite_dispensa: number;
  acima_limite: boolean;
  orgao_saude: boolean;
  periodo: string;
  isento_legalmente?: boolean;
}

export async function countsByYear(
  years: number[],
  empresaIds?: string[] | null
): Promise<Record<number, number>> {
  const result: Record<number, number> = {};
  for (const y of years) result[y] = 0;

  try {
    let q = sql`
      SELECT ano, licitacao_numero, valor_contrato, numero_obra, tipo_obra, objeto
      FROM fct_contratos
      WHERE ano = ANY(${years})
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    for (const r of rows) {
      const licNum = String(r.licitacao_numero ?? "").trim();
      if (licNum !== "") continue;

      const y = Number(r.ano);
      const val = parseFloat(String(r.valor_contrato ?? "0").replace(",", ".")) || 0;
      const th = dispensationThreshold(r.numero_obra, r.tipo_obra, r.objeto);

      if (val > th) {
        result[y] = (result[y] || 0) + 1;
      }
    }
  } catch {}

  return result;
}

export async function totalsSemLicitacaoPorAno(
  years: number[],
  empresaIds?: string[] | null
): Promise<Record<number, number>> {
  const result: Record<number, number> = {};
  for (const y of years) result[y] = 0;

  try {
    let q = sql`
      SELECT ano, licitacao_numero
      FROM fct_contratos
      WHERE ano = ANY(${years})
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    for (const r of (res.rows as any[]) || []) {
      const licNum = String(r.licitacao_numero ?? "").trim();
      if (licNum === "") {
        const y = Number(r.ano);
        result[y] = (result[y] || 0) + 1;
      }
    }
  } catch {}

  return result;
}

export async function getLicitacaoGaps(
  year: number,
  empresaIds?: string[] | null
): Promise<ContratoSemLicitacao[]> {
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
    const list: ContratoSemLicitacao[] = [];

    for (const r of (res.rows as any[]) || []) {
      const licNum = String(r.licitacao_numero ?? "").trim();
      if (licNum !== "") continue;

      const emp = String(r.empresa ?? "");
      const val = parseFloat(String(r.valor_contrato ?? "0").replace(",", ".")) || 0;
      const th = dispensationThreshold(r.numero_obra, r.tipo_obra, r.objeto);
      const mStr = String(r.mes ?? "").padStart(2, "0");

      list.push({
        ano: Number(r.ano),
        empresa: emp,
        numero: String(r.numero ?? ""),
        fornecedor: String(r.fornecedor ?? ""),
        objeto: String(r.objeto ?? ""),
        valor_contrato: String(r.valor_contrato ?? "0"),
        licitacao_numero: licNum,
        mes: Number(r.mes),
        numero_obra: r.numero_obra ?? null,
        tipo_obra: r.tipo_obra ?? null,
        modalidade: r.modalidade ?? null,
        fundlegal: r.fundlegal ?? null,
        limite_dispensa: th,
        acima_limite: val > th,
        orgao_saude: emp === SAUDE_EMPRESA,
        periodo: `${mStr}/${r.ano}`,
      });
    }

    return list;
  } catch {
    return [];
  }
}
