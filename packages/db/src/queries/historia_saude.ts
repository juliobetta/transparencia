import { sql } from "kysely";
import { db } from "../client";
import { SAUDE_EMPRESA } from "./licitacao_gaps";

export interface EmendaSaude {
  Nº: string;
  Objeto: string;
  "Valor Autorizado": number;
  Empenhado: number | null;
  Autor: string;
  "Tipo da Emenda": string;
  "Esfera de Origem": string;
  "Ato Normativo": string;
  Destinação: string;
}

export interface BudgetSaude {
  dotacao: number;
  empenhado: number;
  taxaExecucao: number;
  alertaSubExecucao: boolean;
}

export interface ExecutionTrendSaude {
  ano: number;
  empenhado: number;
}

export interface HistoriaSaudeResult {
  emendas: EmendaSaude[];
  emendasTotal: number;
  orcamento: BudgetSaude;
  executionTrend: ExecutionTrendSaude[];
}

export async function getHistoriaSaude(
  year: number,
  empresaIds?: string[] | string | null,
): Promise<HistoriaSaudeResult> {
  const targetEmpresas = Array.isArray(empresaIds)
    ? empresaIds.length > 0
      ? empresaIds
      : [SAUDE_EMPRESA]
    : typeof empresaIds === "string"
      ? [empresaIds]
      : [SAUDE_EMPRESA];

  const emendas: EmendaSaude[] = [];
  let emendasTotal = 0;

  try {
    const resE = await sql`
      SELECT numero_emenda AS "Nº", resumo AS "Objeto", valor_total AS "Valor Autorizado",
             empenhado AS "Empenhado", autor AS "Autor", tipo_emenda AS "Tipo da Emenda",
             esfera_origem AS "Esfera de Origem", ato_normativo AS "Ato Normativo", destinacao AS "Destinação"
      FROM fct_emendas
      WHERE ano = ${year} AND empresa_id = ANY(${targetEmpresas})
    `.execute(db);

    const rowsE = (resE.rows as any[]) || [];
    for (const r of rowsE) {
      const valAut =
        parseFloat(String(r["Valor Autorizado"] ?? "0").replace(",", ".")) || 0;
      const emp = parseFloat(String(r.Empenhado ?? "0").replace(",", ".")) || 0;
      emendasTotal += valAut;
      emendas.push({
        Nº: String(r.Nº ?? ""),
        Objeto: String(r.Objeto ?? ""),
        "Valor Autorizado": valAut,
        Empenhado: emp > 0 ? emp : null,
        Autor: String(r.Autor ?? ""),
        "Tipo da Emenda": String(r["Tipo da Emenda"] ?? ""),
        "Esfera de Origem": String(r["Esfera de Origem"] ?? ""),
        "Ato Normativo": String(r["Ato Normativo"] ?? ""),
        Destinação: String(r.Destinação ?? ""),
      });
    }
  } catch {}

  let orcamento: BudgetSaude = {
    dotacao: 0,
    empenhado: 0,
    taxaExecucao: 0,
    alertaSubExecucao: false,
  };
  try {
    const resB = await sql`
      SELECT empenhado, dotacao_atualizada
      FROM fct_despesas_por_orgao
      WHERE ano = ${year} AND empresa = ANY(${targetEmpresas})
    `.execute(db);

    let dot = 0;
    let emp = 0;
    for (const r of (resB.rows as any[]) || []) {
      dot +=
        parseFloat(String(r.dotacao_atualizada ?? "0").replace(",", ".")) || 0;
      emp += parseFloat(String(r.empenhado ?? "0").replace(",", ".")) || 0;
    }
    const taxa = dot > 0 ? emp / dot : 0;
    const currentYear = new Date().getFullYear();
    orcamento = {
      dotacao: dot,
      empenhado: emp,
      taxaExecucao: taxa,
      alertaSubExecucao: taxa < 0.7 && year < currentYear,
    };
  } catch {}

  let executionTrend: ExecutionTrendSaude[] = [];
  try {
    const resT = await sql`
      SELECT ano, SUM(CAST(REPLACE(empenhado, ',', '.') AS numeric)) AS empenhado
      FROM fct_despesas_por_orgao
      WHERE empresa = ANY(${targetEmpresas})
      GROUP BY ano
      ORDER BY ano
    `.execute(db);
    executionTrend = ((resT.rows as any[]) || []).map((r) => ({
      ano: Number(r.ano),
      empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
    }));
  } catch {}

  return {
    emendas,
    emendasTotal,
    orcamento,
    executionTrend,
  };
}
