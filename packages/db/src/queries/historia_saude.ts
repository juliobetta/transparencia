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
      WHERE ano = ${year} AND empresa_id = ANY(${targetEmpresas})
    `.execute(db);

    const rowsE = (resE.rows as Record<string, unknown>[]) || [];
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

  let medicamentosInsumos = 0;
  let judicializacao = 0;

  try {
    const resSub = await sql`
      SELECT
        subfuncao_nome,
        elemento,
        SUM(CAST(REPLACE(empenhado, ',', '.') AS numeric)) AS empenhado
      FROM fct_despesas
      WHERE ano = ${year} AND empresa_id = ANY(${targetEmpresas})
      GROUP BY subfuncao_nome, elemento
    `.execute(db);

    for (const r of (resSub.rows as Record<string, unknown>[]) || []) {
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const sub = String(r.subfuncao_nome ?? "").toLowerCase();
      const elem = String(r.elemento ?? "").toLowerCase();

      if (
        sub.includes("303") ||
        sub.includes("farmac") ||
        sub.includes("profilat")
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
  } catch {}

  let orcamento: BudgetSaude = {
    dotacao: 0,
    empenhado: 0,
    taxaExecucao: 0,
    alertaSubExecucao: false,
    medicamentosInsumos,
  };
  try {
    const resB = await sql`
      SELECT empenhado, dotacao_atualizada
      FROM fct_despesas_por_orgao
      WHERE ano = ${year} AND empresa = ANY(${targetEmpresas})
    `.execute(db);

    let dot = 0;
    let emp = 0;
    for (const r of (resB.rows as Record<string, unknown>[]) || []) {
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
      medicamentosInsumos,
    };
  } catch {}

  let fontesReceita: FontesReceitaSaude = {
    uniaoSusPct: 0,
    estadoPct: 0,
    propriaPct: 0,
    repassesPrefeitura: 0,
    emendasParlamentares: emendasTotal,
  };

  try {
    const resR = await sql`
      SELECT
        tipo_receita,
        codigo,
        SUM(CAST(REPLACE(arrecadado, ',', '.') AS numeric)) AS arrecadado
      FROM fct_receitas
      WHERE ano = ${year} AND empresa_id = ANY(${targetEmpresas})
      GROUP BY tipo_receita, codigo
    `.execute(db);

    let totalR = 0;
    let uniaoR = 0;
    let estadoR = 0;
    let repassesPref = 0;

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

    const uniaoSusPct = totalR > 0 ? (uniaoR / totalR) * 100 : 0;
    const estadoPct = totalR > 0 ? (estadoR / totalR) * 100 : 0;
    const propriaPct =
      totalR > 0 ? Math.max(0, 100 - uniaoSusPct - estadoPct) : 0;

    fontesReceita = {
      uniaoSusPct,
      estadoPct,
      propriaPct,
      repassesPrefeitura: repassesPref,
      emendasParlamentares: emendasTotal,
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
    executionTrend = ((resT.rows as Record<string, unknown>[]) || []).map(
      (r) => ({
        ano: Number(r.ano),
        empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
      }),
    );
  } catch {}

  let hhi = 0;
  let hhiClassificacao = "baixa";

  try {
    const resHHI = await sql`
      SELECT f.descricao, SUM(CAST(REPLACE(f.empenhado, ',', '.') AS numeric)) AS empenhado
      FROM fct_despesas_por_fornecedor f
      WHERE f.ano = ${year} AND f.empresa = ANY(${targetEmpresas})
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

    if (hhi >= 2500) {
      hhiClassificacao = "moderada a alta";
    } else if (hhi >= 1500) {
      hhiClassificacao = "moderada";
    } else {
      hhiClassificacao = "baixa";
    }
  } catch {}

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
