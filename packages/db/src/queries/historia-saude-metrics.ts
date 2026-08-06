import { sql } from "kysely";
import { db } from "../client";
import {
  getAdesaoDeAtaMetrics,
  getAdesaoExternaMetrics,
  getDistribucaoModalidadesMetrics,
} from "./licitacoes-metrics";

export interface HistoriaSaudeMetricsDTO {
  historiaSaudeId: string;
  portalSlug: string;
  ano: number;
  dotacaoTotal: number;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  medicamentosInsumosEmpenhado: number;
  medicamentosInsumosPago: number;
  judicializacaoEmpenhado: number;
  judicializacaoPago: number;
  emendasSaudeArrecadado: number;
  hhiConcentracaoFornecedores: number;
}

export interface EmendaSaudeDTO {
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

export interface EmendasStatsSaudeDTO {
  totalAutorizado: number;
  totalEmpenhado: number;
  taxaEmpenho: number;
  maiorEmenda: number;
  lista: EmendaSaudeDTO[];
}

export interface FontesReceitaSaudeDTO {
  uniaoSusPct: number;
  estadoPct: number;
  propriaPct: number;
  repassesPrefeitura: number;
  emendasParlamentares: number;
}

export interface LicitacoesSaudeResultDTO {
  adesaoCaronaCount: number;
  adesaoCaronaValor: number;
  empenhosAtaExternaCount: number;
  pagoAtaExternaValor: number;
  modalidades: Array<{ nome: string; valor: number; pct: number }>;
}

export async function getHistoriaSaudeMetrics(
  portalSlug: string,
  ano: number,
): Promise<HistoriaSaudeMetricsDTO | null> {
  try {
    const result = await db
      .selectFrom("fct_historia_saude_metricas")
      .selectAll()
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .executeTakeFirst();

    if (!result) return null;

    return {
      historiaSaudeId: result.historia_saude_id,
      portalSlug: result.portal_slug,
      ano: Number(result.ano),
      dotacaoTotal: Number(result.dotacao_total ?? 0),
      totalEmpenhado: Number(result.total_empenhado ?? 0),
      totalLiquidado: Number(result.total_liquidado ?? 0),
      totalPago: Number(result.total_pago ?? 0),
      medicamentosInsumosEmpenhado: Number(
        result.medicamentos_insumos_empenhado ?? 0,
      ),
      medicamentosInsumosPago: Number(result.medicamentos_insumos_pago ?? 0),
      judicializacaoEmpenhado: Number(result.judicializacao_empenhado ?? 0),
      judicializacaoPago: Number(result.judicializacao_pago ?? 0),
      emendasSaudeArrecadado: Number(result.emendas_saude_arrecadado ?? 0),
      hhiConcentracaoFornecedores: Number(
        result.hhi_concentracao_fornecedores ?? 0,
      ),
    } satisfies HistoriaSaudeMetricsDTO;
  } catch {
    return null;
  }
}

export async function getSaudeExecutionTrendMetrics(
  portalSlug: string,
): Promise<Array<{ ano: number; empenhado: number }>> {
  try {
    const results = await db
      .selectFrom("fct_historia_saude_metricas")
      .select(["ano", "total_empenhado as empenhado"])
      .where("portal_slug", "=", portalSlug)
      .orderBy("ano", "asc")
      .execute();

    return results.map((r) => ({
      ano: Number(r.ano),
      empenhado: Number(r.empenhado ?? 0),
    }));
  } catch {
    return [];
  }
}

export async function getSaudeEmendasMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<EmendasStatsSaudeDTO> {
  const empty: EmendasStatsSaudeDTO = {
    totalAutorizado: 0,
    totalEmpenhado: 0,
    taxaEmpenho: 0,
    maiorEmenda: 0,
    lista: [],
  };

  if (empresaIds.length === 0) return empty;

  try {
    const rows = await db
      .selectFrom("fct_emendas")
      .selectAll()
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where((eb) =>
        eb.or([
          eb("empresa_id", "in", empresaIds),
          eb("destinacao", "ilike", "%saud%"),
          eb("resumo", "ilike", "%saud%"),
        ]),
      )
      .execute();

    let totalAutorizado = 0;
    let totalEmpenhado = 0;
    let maiorEmenda = 0;
    const lista: EmendaSaudeDTO[] = [];

    for (const r of rows) {
      const valAut = Number(r.valor_total ?? 0);
      const emp = Number(r.empenhado ?? 0);

      totalAutorizado += valAut;
      totalEmpenhado += emp;
      if (valAut > maiorEmenda) maiorEmenda = valAut;

      lista.push({
        id: `${r.autor ?? ""}-${r.resumo ?? ""}-${r.numero_emenda ?? ""}-${lista.length}`,
        Nº: String(r.numero_emenda ?? ""),
        Objeto: String(r.resumo ?? ""),
        "Valor Autorizado": valAut,
        Empenhado: emp > 0 ? emp : null,
        Autor: String(r.autor ?? ""),
        "Tipo da Emenda": String(r.tipo_emenda ?? ""),
        "Esfera de Origem": String(r.esfera_origem ?? ""),
        "Ato Normativo": String(r.ato_normativo ?? ""),
        Destinação: String(r.destinacao ?? ""),
      });
    }

    return {
      totalAutorizado,
      totalEmpenhado,
      taxaEmpenho: totalAutorizado > 0 ? totalEmpenhado / totalAutorizado : 0,
      maiorEmenda,
      lista,
    };
  } catch {
    return empty;
  }
}

export async function getSaudeContratosCountMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<number> {
  if (empresaIds.length === 0) return 0;

  try {
    const res = await db
      .selectFrom("fct_contratos")
      .select((eb) => eb.fn.count<string>("contrato_id").as("count"))
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where((eb) =>
        eb.or([
          eb("empresa_id", "in", empresaIds),
          eb("objeto", "ilike", "%saud%"),
          eb("modalidade", "ilike", "%saud%"),
        ]),
      )
      .executeTakeFirst();

    return Number(res?.count ?? 0);
  } catch {
    return 0;
  }
}

export async function getSaudeFornecedoresCountMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<number> {
  if (empresaIds.length === 0) return 0;

  try {
    const res = await db
      .selectFrom("fct_despesas")
      .select(sql<number>`count(distinct fornecedor_nome)`.as("count"))
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where((eb) =>
        eb.or([
          eb("empresa_id", "in", empresaIds),
          eb("fornecedor_nome", "ilike", "%saud%"),
          eb("fornecedor_nome", "ilike", "%hospital%"),
          eb("fornecedor_nome", "ilike", "%farmac%"),
        ]),
      )
      .executeTakeFirst();

    return Number(res?.count ?? 0);
  } catch {
    return 0;
  }
}

export async function getSaudeFontesReceitaMetrics(params: {
  portalSlug: string;
  ano: number;
  empresaIds: string[];
  empenhadoTotal: number;
}): Promise<FontesReceitaSaudeDTO> {
  const { portalSlug, ano, empresaIds, empenhadoTotal } = params;
  const empty: FontesReceitaSaudeDTO = {
    uniaoSusPct: 0,
    estadoPct: 0,
    propriaPct: 0,
    repassesPrefeitura: 0,
    emendasParlamentares: 0,
  };

  if (empresaIds.length === 0) return empty;

  try {
    const resR = await db
      .selectFrom("fct_receitas")
      .select(["tipo_receita", "codigo", "descricao", "arrecadado"])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where("empresa_id", "in", empresaIds)
      .execute();

    let uniaoR = 0;
    let estadoR = 0;
    let intraR = 0;

    for (const r of resR) {
      const val = Number(r.arrecadado ?? 0);
      if (val <= 0) continue;

      const tipo = (r.tipo_receita ?? "").toLowerCase();
      const rawCod = r.codigo ?? "";
      const codClean = rawCod.replace(/\./g, "");
      const desc = (r.descricao ?? "").toLowerCase();

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

    const repassesPref =
      intraR > 0 ? intraR : Math.max(0, empenhadoTotal - uniaoR - estadoR);
    const baseCalculo = Math.max(
      empenhadoTotal,
      uniaoR + estadoR + repassesPref,
    );
    let uniaoSusPct = 0;
    let estadoPct = 0;
    let propriaPct = 0;

    if (baseCalculo > 0) {
      uniaoSusPct = Math.round((uniaoR / baseCalculo) * 100);
      estadoPct = Math.round((estadoR / baseCalculo) * 100);
      propriaPct = Math.max(0, 100 - uniaoSusPct - estadoPct);
    }

    return {
      uniaoSusPct,
      estadoPct,
      propriaPct,
      repassesPrefeitura: repassesPref,
      emendasParlamentares: 0,
    };
  } catch {
    return empty;
  }
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

export async function getSaudeLicitacoesMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<LicitacoesSaudeResultDTO> {
  const empty: LicitacoesSaudeResultDTO = {
    adesaoCaronaCount: 0,
    adesaoCaronaValor: 0,
    empenhosAtaExternaCount: 0,
    pagoAtaExternaValor: 0,
    modalidades: [],
  };

  if (empresaIds.length === 0) return empty;

  try {
    const adesao = await getAdesaoDeAtaMetrics(portalSlug, ano, empresaIds);
    const adesaoExterna = await getAdesaoExternaMetrics(
      portalSlug,
      ano,
      empresaIds,
    );
    const distModalidades = await getDistribucaoModalidadesMetrics(
      portalSlug,
      ano,
      empresaIds,
    );

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

    const modalidades = Object.entries(modalityTotals).map(([nome, valor]) => ({
      nome,
      valor,
      pct: totalModalityValue > 0 ? (valor / totalModalityValue) * 100 : 0,
    }));

    return {
      adesaoCaronaCount: adesao.quantidade,
      adesaoCaronaValor: adesao.valor,
      empenhosAtaExternaCount: adesaoExterna.quantidade,
      pagoAtaExternaValor: adesaoExterna.totalPago,
      modalidades,
    };
  } catch {
    return empty;
  }
}
