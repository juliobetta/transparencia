import { sql } from "kysely";
import { db } from "../client";

export interface ItemAdesaoAta {
  numero: string;
  objeto: string;
  licitacao_valor: number;
  carona: string;
  total_c_valor: number;
  total_c_empenhado: number;
  mes: number | null;
  tem_contrato: boolean;
  periodo: string;
}

export interface AdesaoAtaResult {
  lista: ItemAdesaoAta[];
  quantidade: number;
  valor: number;
  total_licitacao: number;
  contratos_associados_count: number;
}

export interface ItemAdesaoExterna {
  data: string;
  fornecedor: string;
  empenhado: number;
  pago: number;
  unidade: string;
  justificativa: string;
  num_licitacao: string;
}

export interface AdesaoExternaResult {
  lista: ItemAdesaoExterna[];
  quantidade: number;
  total_pago: number;
}

export async function getAdesaoDeAta(
  year: number,
  empresaIds?: string[] | null,
): Promise<AdesaoAtaResult> {
  try {
    let q = sql`
      SELECT
        l.licitacao_numero AS numero,
        COALESCE(l.discriminacao, l.licitacao_numero) AS objeto,
        l.valor AS licitacao_valor,
        l.carona,
        c.mes,
        COALESCE(c.valor_contrato, 0) AS c_valor,
        COALESCE(c.empenhado, 0) AS c_empenhado
      FROM fct_licitacoes l
      LEFT JOIN fct_contratos c
        ON c.licitacao_numero = l.licitacao_numero
        AND c.empresa_id = l.empresa_id
      WHERE l.ano = ${year} AND l.carona = 'S'
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND l.empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    if (rows.length === 0) {
      return {
        lista: [],
        quantidade: 0,
        valor: 0,
        total_licitacao: 0,
        contratos_associados_count: 0,
      };
    }

    const map: Record<
      string,
      {
        numero: string;
        objeto: string;
        licitacao_valor: number;
        carona: string;
        total_c_valor: number;
        total_c_empenhado: number;
        mes: number | null;
      }
    > = {};

    for (const r of rows) {
      const key = `${r.numero}__${r.objeto}`;
      const licVal =
        parseFloat(String(r.licitacao_valor ?? "0").replace(",", ".")) || 0;
      const cVal = parseFloat(String(r.c_valor ?? "0").replace(",", ".")) || 0;
      const cEmp =
        parseFloat(String(r.c_empenhado ?? "0").replace(",", ".")) || 0;
      const mesNum =
        r.mes !== null && r.mes !== undefined ? Number(r.mes) : null;

      if (!map[key]) {
        map[key] = {
          numero: String(r.numero ?? ""),
          objeto: String(r.objeto ?? ""),
          licitacao_valor: licVal,
          carona: String(r.carona ?? "S"),
          total_c_valor: 0,
          total_c_empenhado: 0,
          mes: mesNum,
        };
      }
      map[key].total_c_valor += cVal;
      map[key].total_c_empenhado += cEmp;
      if (map[key].mes === null && mesNum !== null) map[key].mes = mesNum;
    }

    const lista: ItemAdesaoAta[] = Object.values(map).map((item) => {
      const mStr = item.mes ? String(item.mes).padStart(2, "0") : "";
      return {
        ...item,
        tem_contrato: item.total_c_valor > 0,
        periodo: mStr ? `${mStr}/${year}` : "",
      };
    });

    const valor = lista.reduce((acc, i) => acc + i.total_c_valor, 0);
    const total_licitacao = lista.reduce(
      (acc, i) => acc + i.licitacao_valor,
      0,
    );
    const contratos_associados_count = lista.filter(
      (i) => i.tem_contrato,
    ).length;

    return {
      lista,
      quantidade: lista.length,
      valor,
      total_licitacao,
      contratos_associados_count,
    };
  } catch {
    return {
      lista: [],
      quantidade: 0,
      valor: 0,
      total_licitacao: 0,
      contratos_associados_count: 0,
    };
  }
}

export async function getAdesaoExterna(
  year: number,
  empresaIds?: string[] | null,
): Promise<AdesaoExternaResult> {
  try {
    let q = sql`
      SELECT
        dg.data_empenho AS data,
        dg.fornecedor_nome AS fornecedor,
        dg.empenhado AS empenhado,
        dg.pago AS pago,
        dg.empresa_id AS unidade,
        dg.descricao AS justificativa,
        dg.licitacao_numero AS num_licitacao
      FROM fct_despesas dg
      WHERE dg.ano = ${year}
        AND (
          UPPER(dg.descricao) LIKE '%ATA DE REGISTRO DE PRE%'
          OR UPPER(dg.descricao) LIKE '%ADESAO%ATA%'
          OR UPPER(dg.descricao) LIKE '%ADESÃO%ATA%'
          OR UPPER(dg.descricao) LIKE '%TERMO DE ADESÃO%'
          OR UPPER(dg.descricao) LIKE '%TERMO DE ADESAO%'
        )
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND dg.empresa_id = ANY(${empresaIds})`;
    }
    q = sql`${q} ORDER BY dg.pago DESC`;

    const res = await q.execute(db);
    const rows = (res.rows as any[]) || [];

    const lista: ItemAdesaoExterna[] = rows.map((r) => {
      const emp = parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
      const pag = parseFloat(String(r.pago ?? "0").replace(",", ".")) || 0;
      return {
        data: String(r.data ?? ""),
        fornecedor: String(r.fornecedor ?? ""),
        empenhado: emp,
        pago: pag,
        unidade: String(r.unidade ?? ""),
        justificativa: String(r.justificativa ?? ""),
        num_licitacao: String(r.num_licitacao ?? ""),
      };
    });

    const total_pago = lista.reduce((acc, i) => acc + i.pago, 0);
    return { lista, quantidade: lista.length, total_pago };
  } catch {
    return { lista: [], quantidade: 0, total_pago: 0 };
  }
}
