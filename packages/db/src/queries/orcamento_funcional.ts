import { sql } from "kysely";
import { db } from "../client";

export interface ItemOrcamentoFuncional {
  funcao_nome: string;
  subfuncao_nome: string;
  dotacao_atualizada: number;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export async function getOrcamentoFuncional(
  year: number,
  empresaIds?: string[] | null
): Promise<ItemOrcamentoFuncional[]> {
  try {
    let q = sql`
      SELECT funcao_nome, subfuncao_nome, dotacao_atualizada, empenhado, liquidado, pago
      FROM fct_despesas
      WHERE ano = ${year} AND funcao_nome IS NOT NULL
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    const map: Record<
      string,
      {
        funcao_nome: string;
        subfuncao_nome: string;
        dotacao_atualizada: number;
        empenhado: number;
        liquidado: number;
        pago: number;
      }
    > = {};

    for (const r of rows) {
      const func = String(r.funcao_nome ?? "");
      const sub = String(r.subfuncao_nome ?? "");
      const key = `${func}__${sub}`;

      const dot = parseFloat(String(r.dotacao_atualizada ?? "0").replace(",", ".")) || 0;
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;

      if (!map[key]) {
        map[key] = {
          funcao_nome: func,
          subfuncao_nome: sub,
          dotacao_atualizada: 0,
          empenhado: 0,
          liquidado: 0,
          pago: 0,
        };
      }
      map[key].dotacao_atualizada += dot;
      map[key].empenhado += emp;
      map[key].liquidado += liq;
      map[key].pago += pag;
    }

    return Object.values(map);
  } catch {
    return [];
  }
}
