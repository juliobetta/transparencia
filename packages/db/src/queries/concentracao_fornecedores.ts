import { sql } from "kysely";
import { db } from "../client";

export interface ItemFornecedorTop {
  codigo: string;
  descricao: string;
  empenhado: number;
  percentual: number;
}

export interface ConcentracaoResult {
  top10: ItemFornecedorTop[];
  hhi: number;
  dominante: string | null;
  total_all: number;
}

const ELEMENTOS_VAL = ["30", "33", "35", "36", "39", "40", "51", "52"];

export async function getConcentracaoFornecedores(
  year: number,
  empresaIds?: string[] | null,
): Promise<ConcentracaoResult> {
  try {
    let q = sql`
      SELECT f.codigo, f.descricao, f.empenhado
      FROM fct_despesas_por_fornecedor f
      LEFT JOIN fct_despesas g
        ON f.ano = g.ano
        AND f.descricao = g.fornecedor_nome
      WHERE f.ano = ${year}
        AND g.elemento = ANY(${ELEMENTOS_VAL})
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND f.empresa = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    const map: Record<
      string,
      { codigo: string; descricao: string; empenhado: number }
    > = {};
    let total = 0;

    for (const r of rows) {
      const cod = String(r.codigo ?? "");
      const desc = String(r.descricao ?? "");
      const key = `${cod}__${desc}`;
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;

      if (!map[key]) {
        map[key] = { codigo: cod, descricao: desc, empenhado: 0 };
      }
      map[key].empenhado += emp;
      total += emp;
    }

    const items = Object.values(map).map((i) => ({
      ...i,
      percentual: total > 0 ? (i.empenhado / total) * 100 : 0,
    }));

    items.sort((a, b) => b.empenhado - a.empenhado);
    const top10 = items.slice(0, 10);

    const sumHHI = items.reduce((acc, i) => {
      const share = total > 0 ? i.empenhado / total : 0;
      return acc + share * share;
    }, 0);
    const hhi = sumHHI * 10000;

    const domItem = items.find((i) => i.percentual > 40);
    const dominante = domItem ? domItem.descricao : null;

    return { top10, hhi, dominante, total_all: total };
  } catch {
    return { top10: [], hhi: 0, dominante: null, total_all: 0 };
  }
}
