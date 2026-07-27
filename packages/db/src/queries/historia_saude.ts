import { sql } from "kysely";
import { db } from "../client";
import { getAdesaoDeAta, getAdesaoExterna } from "./adesao_de_ata";
import { getDistribucaoModalidades, SAUDE_EMPRESA } from "./licitacao_gaps";

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
  liquidado: number;
  pago: number;
  taxaExecucao: number;
  alertaSubExecucao: boolean;
  medicamentosInsumos: number;
  contratosVinculadosCount: number;
  fornecedoresAtivosCount: number;
}

export interface ExecutionTrendSaude {
  ano: number;
  empenhado: number;
}

export interface EmendaSaude {
  id: string;
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

export interface LicitacaoModalidadeItem {
  nome: string;
  valor: number;
  pct: number;
}

export interface LicitacoesSaudeResult {
  adesaoCaronaCount: number;
  adesaoCaronaValor: number;
  empenhosAtaExternaCount: number;
  pagoAtaExternaValor: number;
  modalidades: LicitacaoModalidadeItem[];
}

export interface EmendasStatsSaude {
  totalAutorizado: number;
  totalEmpenhado: number;
  taxaEmpenho: number;
  maiorEmenda: number;
  lista: EmendaSaude[];
}

export interface HistoriaSaudeResult {
  orcamento: BudgetSaude;
  fontesReceita: FontesReceitaSaude;
  executionTrend: ExecutionTrendSaude[];
  farmaceutica: AssistenciaFarmaceuticaSaude;
  licitacoesSaude: LicitacoesSaudeResult;
  emendasStats: EmendasStatsSaude;
  emendas: EmendaSaude[];
  emendasTotal: number;
}

function normalizeModalidadeName(
  rawName: string,
  carona: string | null,
): string {
  const norm = rawName
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  if (carona === "S" || norm.includes("carona") || norm.includes("adesao")) {
    return "Adesão a ata (carona)";
  }
  if (norm.includes("pregao eletronico")) {
    return "Pregão eletrônico";
  }
  if (norm.includes("dispensa")) {
    return "Dispensa de licitação";
  }
  if (norm.includes("inexig")) {
    return "Inexigibilidade";
  }
  return "Tomada de preços / outros";
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
  let emendasEmpenhadoTotal = 0;
  let maiorEmenda = 0;

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
      emendasEmpenhadoTotal += emp;
      if (valAut > maiorEmenda) {
        maiorEmenda = valAut;
      }

      emendas.push({
        id: `${r.Autor ?? ""}-${r.Objeto ?? ""}-${r.Nº ?? ""}-${emendas.length}`,
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

  const emendasStats: EmendasStatsSaude = {
    totalAutorizado: emendasTotal,
    totalEmpenhado: emendasEmpenhadoTotal,
    taxaEmpenho: emendasTotal > 0 ? emendasEmpenhadoTotal / emendasTotal : 0,
    maiorEmenda,
    lista: emendas,
  };

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
  let liq = 0;
  let pag = 0;

  try {
    const resB = await sql`
      SELECT
        SUM(empenhado) AS empenhado,
        SUM(liquidado) AS liquidado,
        SUM(pago) AS pago,
        SUM(dotacao_atualizada) AS dotacao_atualizada
      FROM fct_despesas_por_orgao
      WHERE ano = ${year} AND (empresa = ANY(${targetEmpresas}) OR codigo LIKE '10%' OR lower(descricao) LIKE '%saú%' OR lower(descricao) LIKE '%saud%')
    `.execute(db);

    for (const r of (resB.rows as Record<string, unknown>[]) || []) {
      dot += parseFloat(String(r.dotacao_atualizada ?? "0")) || 0;
      emp += parseFloat(String(r.empenhado ?? "0")) || 0;
      liq += parseFloat(String(r.liquidado ?? "0")) || 0;
      pag += parseFloat(String(r.pago ?? "0")) || 0;
    }
  } catch (_e) {}

  if (dot === 0 && emp === 0) {
    try {
      const resFallback = await sql`
        SELECT
          SUM(empenhado) AS empenhado,
          SUM(liquidado) AS liquidado,
          SUM(pago) AS pago,
          SUM(dotacao_atualizada) AS dotacao_atualizada
        FROM fct_despesas
        WHERE ano = ${year} AND (funcao = '10' OR empresa_id = ANY(${targetEmpresas}))
      `.execute(db);
      for (const r of (resFallback.rows as Record<string, unknown>[]) || []) {
        dot += parseFloat(String(r.dotacao_atualizada ?? "0")) || 0;
        emp += parseFloat(String(r.empenhado ?? "0")) || 0;
        liq += parseFloat(String(r.liquidado ?? "0")) || 0;
        pag += parseFloat(String(r.pago ?? "0")) || 0;
      }
    } catch (_e) {}
  }

  let contratosVinculadosCount = 0;
  try {
    const resC = await sql`
      SELECT COUNT(*)::int AS count
      FROM fct_contratos
      WHERE ano = ${year} AND (empresa_id = ANY(${targetEmpresas}) OR lower(objeto) LIKE '%saud%' OR lower(modalidade) LIKE '%saud%')
    `.execute(db);
    const row = resC.rows[0] as Record<string, unknown> | undefined;
    contratosVinculadosCount = Number(row?.count ?? 0);
  } catch (_e) {}

  let uniaoSusPct = 0;
  let estadoPct = 0;
  let propriaPct = 0;
  let repassesPref = 0;

  try {
    const resR = await sql`
      SELECT
        tipo_receita,
        codigo,
        descricao,
        arrecadado
      FROM fct_receitas
      WHERE ano = ${year} AND empresa_id = ANY(${targetEmpresas})
    `.execute(db);

    let uniaoR = 0;
    let estadoR = 0;
    let intraR = 0;

    for (const r of (resR.rows as Record<string, unknown>[]) || []) {
      const val = parseFloat(String(r.arrecadado ?? "0")) || 0;
      if (val <= 0) continue;

      const tipo = String(r.tipo_receita ?? "").toLowerCase();
      const rawCod = String(r.codigo ?? "");
      const codClean = rawCod.replace(/\./g, "");
      const desc = String(r.descricao ?? "").toLowerCase();

      if (
        tipo === "uniao" ||
        codClean.startsWith("171") ||
        codClean.startsWith("241") ||
        desc.includes("sus") ||
        desc.includes("união") ||
        desc.includes("uniao")
      ) {
        if (
          codClean === "171300000000" ||
          (!rawCod.endsWith(".00.00") && codClean.startsWith("171"))
        ) {
          if (codClean === "171300000000") {
            uniaoR = Math.max(uniaoR, val);
          } else {
            uniaoR += val;
          }
        }
      } else if (
        tipo === "estado" ||
        codClean.startsWith("172") ||
        codClean.startsWith("242") ||
        desc.includes("estado")
      ) {
        if (codClean === "172000000000") {
          estadoR = Math.max(estadoR, val);
        } else {
          estadoR += val;
        }
      } else if (
        tipo === "intra" ||
        codClean.startsWith("175") ||
        codClean.startsWith("275") ||
        desc.includes("intra") ||
        desc.includes("repasse")
      ) {
        intraR += val;
      }
    }

    repassesPref = intraR > 0 ? intraR : Math.max(0, emp - uniaoR - estadoR);

    const baseCalculo = Math.max(emp, uniaoR + estadoR + repassesPref);
    if (baseCalculo > 0) {
      uniaoSusPct = Math.round((uniaoR / baseCalculo) * 100);
      estadoPct = Math.round((estadoR / baseCalculo) * 100);
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
  let fornecedoresAtivosCount = 0;

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

    fornecedoresAtivosCount = supplierEmpenhados.length;

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

  const taxa = dot > 0 ? emp / dot : 0;
  const currentYear = new Date().getFullYear();
  const orcamento: BudgetSaude = {
    dotacao: dot,
    empenhado: emp,
    liquidado: liq,
    pago: pag,
    taxaExecucao: taxa,
    alertaSubExecucao: taxa < 0.7 && year < currentYear,
    medicamentosInsumos,
    contratosVinculadosCount,
    fornecedoresAtivosCount,
  };

  // Reusando as queries unificadas de licitação e adesão de ata para garantir 100% de paridade com a página de Licitações
  const adesao = await getAdesaoDeAta(year, targetEmpresas);
  const adesaoExterna = await getAdesaoExterna(year, targetEmpresas);
  const distModalidades = await getDistribucaoModalidades(year, targetEmpresas);

  const modalityTotals: Record<string, number> = {
    "Pregão eletrônico": 0,
    "Adesão a ata (carona)": 0,
    "Dispensa de licitação": 0,
    Inexigibilidade: 0,
    "Tomada de preços / outros": 0,
  };

  for (const item of distModalidades) {
    const modGroup = normalizeModalidadeName(item.modalidade, "N");
    modalityTotals[modGroup] =
      (modalityTotals[modGroup] || 0) + item.valorTotal;
  }

  if (adesao.valor > 0) {
    modalityTotals["Adesão a ata (carona)"] = Math.max(
      modalityTotals["Adesão a ata (carona)"],
      adesao.valor,
    );
  }

  const totalModalityValue = Object.values(modalityTotals).reduce(
    (a, b) => a + b,
    0,
  );

  const modalidades: LicitacaoModalidadeItem[] = Object.entries(
    modalityTotals,
  ).map(([nome, valor]) => ({
    nome,
    valor,
    pct: totalModalityValue > 0 ? (valor / totalModalityValue) * 100 : 0,
  }));

  const licitacoesSaude: LicitacoesSaudeResult = {
    adesaoCaronaCount: adesao.quantidade,
    adesaoCaronaValor: adesao.valor,
    empenhosAtaExternaCount: adesaoExterna.quantidade,
    pagoAtaExternaValor: adesaoExterna.totalPago,
    modalidades,
  };

  return {
    orcamento,
    fontesReceita,
    executionTrend,
    farmaceutica,
    licitacoesSaude,
    emendasStats,
    emendas,
    emendasTotal,
  };
}
