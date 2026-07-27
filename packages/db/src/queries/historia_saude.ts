import { sql } from "kysely";
import { db } from "../client";
import { SAUDE_EMPRESA } from "./licitacao_gaps";

export interface FontesReceitaSaude {
  uniaoSusPct: number;
  estadoPct: number;
  propriaPct: number;
  repassesPrefeitura: number;
  emendasParlamentares: number;
}

export interface AssistenciaFarmaceuticaSaude {
  medicamentosInsumos: number; // Subfunção 10.303
  judicializacao: number; // Sentenças judiciais na saúde
  hhi: number; // Concentração HHI
  hhiClassificacao: string; // Ex: "moderada a alta"
}

export interface BudgetSaude {
  dotacao: number;
  empenhado: number;
  taxaExecucao: number;
  alertaSubExecucao: boolean;
  medicamentosInsumos: number;
}

export interface ExecutionTrendSaude {
  ano: number;
  empenhado: number;
}

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

export interface HistoriaSaudeResult {
  orcamento: BudgetSaude;
  fontesReceita: FontesReceitaSaude;
  executionTrend: ExecutionTrendSaude[];
  farmaceutica: AssistenciaFarmaceuticaSaude;
  emendas: EmendaSaude[];
  emendasTotal: number;
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
      WHERE ano = ${year} AND (empresa_id = ANY(${targetEmpresas}) OR lower(destinacao) LIKE '%saud%' OR lower(resumo) LIKE '%saud%')
    `.execute(db);

    const rowsE = (resE.rows as Record<string, unknown>[]) || [];
    for (const r of rowsE) {
      const valAut =
        typeof r["Valor Autorizado"] === "number"
          ? (r["Valor Autorizado"] as number)
          : parseFloat(String(r["Valor Autorizado"] ?? "0")) || 0;
      const emp =
        typeof r.Empenhado === "number"
          ? (r.Empenhado as number)
          : parseFloat(String(r.Empenhado ?? "0")) || 0;
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
  } catch (_e) {}

  let medicamentosInsumos = 0;
  let judicializacao = 0;

  try {
    const resSub = await sql`
      SELECT
        subfuncao,
        subfuncao_nome,
        elemento,
        SUM(empenhado) AS empenhado
      FROM fct_despesas
      WHERE ano = ${year} AND (empresa_id = ANY(${targetEmpresas}) OR funcao = '10')
      GROUP BY subfuncao, subfuncao_nome, elemento
    `.execute(db);

    for (const r of (resSub.rows as Record<string, unknown>[]) || []) {
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const subCode = String(r.subfuncao ?? "");
      const sub = String(r.subfuncao_nome ?? "").toLowerCase();
      const elem = String(r.elemento ?? "").toLowerCase();

      if (
        subCode === "303" ||
        sub.includes("303") ||
        sub.includes("farmac") ||
        sub.includes("profilat") ||
        sub.includes("medicam")
      ) {
        medicamentosInsumos += emp;
      }
      if (
        elem.includes("91") ||
        elem.includes("senten") ||
        elem.includes("judici")
      ) {
        judicializacao += emp;
      }
    }
  } catch (_e) {}

  let dot = 0;
  let emp = 0;

  try {
    const resB = await sql`
      SELECT
        SUM(empenhado) AS empenhado,
        SUM(dotacao_atualizada) AS dotacao_atualizada
      FROM fct_despesas_por_orgao
      WHERE ano = ${year} AND (empresa = ANY(${targetEmpresas}) OR codigo LIKE '10%' OR lower(descricao) LIKE '%saú%' OR lower(descricao) LIKE '%saud%')
    `.execute(db);

    for (const r of (resB.rows as Record<string, unknown>[]) || []) {
      dot += parseFloat(String(r.dotacao_atualizada ?? "0")) || 0;
      emp += parseFloat(String(r.empenhado ?? "0")) || 0;
    }
  } catch (_e) {}

  // Fallback if fct_despesas_por_orgao has no entries for this company
  if (dot === 0 && emp === 0) {
    try {
      const resFallback = await sql`
        SELECT
          SUM(empenhado) AS empenhado,
          SUM(dotacao_atualizada) AS dotacao_atualizada
        FROM fct_despesas
        WHERE ano = ${year} AND (funcao = '10' OR empresa_id = ANY(${targetEmpresas}))
      `.execute(db);
      for (const r of (resFallback.rows as Record<string, unknown>[]) || []) {
        dot += parseFloat(String(r.dotacao_atualizada ?? "0")) || 0;
        emp += parseFloat(String(r.empenhado ?? "0")) || 0;
      }
    } catch (_e) {}
  }

  const taxa = dot > 0 ? emp / dot : 0;
  const currentYear = new Date().getFullYear();
  const orcamento: BudgetSaude = {
    dotacao: dot,
    empenhado: emp,
    taxaExecucao: taxa,
    alertaSubExecucao: taxa < 0.7 && year < currentYear,
    medicamentosInsumos,
  };

  let uniaoSusPct = 0;
  let estadoPct = 0;
  let propriaPct = 0;
  let repassesPref = 0;

  try {
    const resR = await sql`
      SELECT
        tipo_receita,
        codigo,
        SUM(arrecadado) AS arrecadado
      FROM fct_receitas
      WHERE ano = ${year} AND (empresa_id = ANY(${targetEmpresas}) OR tipo_receita IN ('uniao', 'estado', 'intra') OR codigo LIKE '17%')
      GROUP BY tipo_receita, codigo
    `.execute(db);

    let totalR = 0;
    let uniaoR = 0;
    let estadoR = 0;

    for (const r of (resR.rows as Record<string, unknown>[]) || []) {
      const val = parseFloat(String(r.arrecadado ?? "0")) || 0;
      const tipo = String(r.tipo_receita ?? "").toLowerCase();
      const cod = String(r.codigo ?? "");

      if (tipo === "intra" || cod.startsWith("17") || cod.startsWith("27")) {
        repassesPref += val;
      }
      if (tipo === "uniao" || cod.startsWith("1718") || cod.startsWith("171")) {
        uniaoR += val;
      } else if (
        tipo === "estado" ||
        cod.startsWith("1728") ||
        cod.startsWith("172")
      ) {
        estadoR += val;
      }
      totalR += val;
    }

    if (totalR > 0) {
      uniaoSusPct = (uniaoR / totalR) * 100;
      estadoPct = (estadoR / totalR) * 100;
      propriaPct = Math.max(0, 100 - uniaoSusPct - estadoPct);
    }
  } catch (_e) {}

  const fontesReceita: FontesReceitaSaude = {
    uniaoSusPct,
    estadoPct,
    propriaPct,
    repassesPrefeitura: repassesPref,
    emendasParlamentares: emendasTotal,
  };

  let executionTrend: ExecutionTrendSaude[] = [];
  try {
    const resT = await sql`
      SELECT ano,
             SUM(empenhado) AS empenhado
      FROM fct_despesas_por_orgao
      WHERE (empresa = ANY(${targetEmpresas}) OR codigo LIKE '10%' OR lower(descricao) LIKE '%saú%' OR lower(descricao) LIKE '%saud%')
      GROUP BY ano
      ORDER BY ano
    `.execute(db);

    executionTrend = ((resT.rows as Record<string, unknown>[]) || []).map(
      (r) => ({
        ano: Number(r.ano),
        empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
      }),
    );
  } catch (_e) {}

  let hhi = 0;
  let hhiClassificacao = "baixa";

  try {
    const resHHI = await sql`
      SELECT f.descricao,
             SUM(f.empenhado) AS empenhado
      FROM fct_despesas_por_fornecedor f
      WHERE f.ano = ${year} AND (f.empresa = ANY(${targetEmpresas}) OR lower(f.descricao) LIKE '%saud%' OR lower(f.descricao) LIKE '%hospital%' OR lower(f.descricao) LIKE '%farmac%')
      GROUP BY f.descricao
    `.execute(db);

    const rows = (resHHI.rows as Record<string, unknown>[]) || [];
    let totalSuppliers = 0;
    const supplierEmpenhados: number[] = [];

    for (const r of rows) {
      const val = parseFloat(String(r.empenhado ?? "0")) || 0;
      if (val > 0) {
        supplierEmpenhados.push(val);
        totalSuppliers += val;
      }
    }

    if (totalSuppliers > 0) {
      const sumHHI = supplierEmpenhados.reduce((acc, val) => {
        const share = val / totalSuppliers;
        return acc + share * share;
      }, 0);
      hhi = Math.round(sumHHI * 10000);
    }
  } catch (_e) {}

  if (hhi >= 2500) {
    hhiClassificacao = "alta";
  } else if (hhi >= 1500) {
    hhiClassificacao = "moderada a alta";
  } else {
    hhiClassificacao = "baixa";
  }

  const farmaceutica: AssistenciaFarmaceuticaSaude = {
    medicamentosInsumos,
    judicializacao,
    hhi,
    hhiClassificacao,
  };

  return {
    orcamento,
    fontesReceita,
    executionTrend,
    farmaceutica,
    emendas,
    emendasTotal,
  };
}
