import { sql } from "kysely";
import { db } from "../client";

export interface ItemExecucaoOrcamentaria {
  ano: number;
  empresa: string;
  codigo: string;
  descricao: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  dotacao_atualizada: number;
  taxa_execucao: number;
  alerta: "N/D" | "baixa" | "excesso" | "normal";
}

export interface ExecucaoSummary {
  total_empenhado: number;
  total_liquidado: number;
  total_pago: number;
  total_dotacao: number;
  saldo_orcamentario: number;
}

export async function getExecucaoOrcamentaria(
  year: number,
  empresaIds?: string[] | null,
): Promise<ItemExecucaoOrcamentaria[]> {
  try {
    let q = sql`
      SELECT ano, empresa, codigo, descricao, empenhado, liquidado, pago, dotacao_atualizada
      FROM fct_despesas_por_orgao
      WHERE ano = ${year}
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    return rows.map((r) => {
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      const dot =
        parseFloat(String(r.dotacao_atualizada ?? "0").replace(",", ".")) || 0;
      const taxa = dot > 0 ? emp / dot : 0;

      let alerta: "N/D" | "baixa" | "excesso" | "normal" = "normal";
      if (emp === 0 && dot === 0 && taxa === 0) {
        alerta = "N/D";
      } else if (taxa < 0.3) {
        alerta = "baixa";
      } else if (taxa > 1.0) {
        alerta = "excesso";
      }

      return {
        ano: Number(r.ano),
        empresa: String(r.empresa ?? ""),
        codigo: String(r.codigo ?? ""),
        descricao: String(r.descricao ?? ""),
        empenhado: emp,
        liquidado: liq,
        pago: pag,
        dotacao_atualizada: dot,
        taxa_execucao: taxa,
        alerta,
      };
    });
  } catch {
    return [];
  }
}

export function summarizeExecucao(
  items: ItemExecucaoOrcamentaria[],
): ExecucaoSummary {
  const total_empenhado = items.reduce((acc, i) => acc + i.empenhado, 0);
  const total_liquidado = items.reduce((acc, i) => acc + i.liquidado, 0);
  const total_pago = items.reduce((acc, i) => acc + i.pago, 0);
  const total_dotacao = items.reduce((acc, i) => acc + i.dotacao_atualizada, 0);
  return {
    total_empenhado,
    total_liquidado,
    total_pago,
    total_dotacao,
    saldo_orcamentario: total_dotacao - total_empenhado,
  };
}
