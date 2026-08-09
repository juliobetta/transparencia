import { sql } from "kysely";
import { db } from "../client";

export interface HistoriaCapremMetricsDTO {
  historiaCapremId: string;
  portalSlug: string;
  ano: number;
  totalAporteExigido: number;
  totalAporteQuitado: number;
  taxaAdimplenciaAporte: number;
  totalEmpenhadoPatronal: number;
  totalLiquidadoPatronal: number;
  totalPagoPatronal: number;
  romboPatronalNaoRepassado: number;
  totalAmortizacaoDivida: number;
  totalCaspPlanoSaude: number;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  servidoresEfetivos: number;
  servidoresTemporarios: number;
}

/**
 * Retorna as métricas da história previdenciária (CAPREM) para o portal de Porciúncula e ano.
 *
 * A história da CAPREM é um apanhado geral atômico exclusivo da Prefeitura de Porciúncula,
 * não possuindo filtro por `empresaIds` (consolida todas as entidades) e retornando `null`
 * para qualquer outro portal.
 */
export async function getHistoriaCapremMetrics(
  portalSlug: string,
  ano: number,
): Promise<HistoriaCapremMetricsDTO | null> {
  const result = await db
    .selectFrom("fct_historia_caprem_metricas")
    .selectAll()
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", ano)
    .executeTakeFirst();

  if (!result) return null;

  return {
    historiaCapremId: result.historia_caprem_id,
    portalSlug: result.portal_slug,
    ano: Number(result.ano),
    totalAporteExigido: Number(result.total_aporte_exigido ?? 0),
    totalAporteQuitado: Number(result.total_aporte_quitado ?? 0),
    taxaAdimplenciaAporte: Number(result.taxa_adimplencia_aporte ?? 0),
    totalEmpenhadoPatronal: Number(result.total_empenhado_patronal ?? 0),
    totalLiquidadoPatronal: Number(result.total_liquidado_patronal ?? 0),
    totalPagoPatronal: Number(result.total_pago_patronal ?? 0),
    romboPatronalNaoRepassado: Number(result.rombo_patronal_nao_repassado ?? 0),
    totalAmortizacaoDivida: Number(result.total_amortizacao_divida ?? 0),
    totalCaspPlanoSaude: Number(result.total_casp_plano_saude ?? 0),
    totalEmpenhado: Number(result.total_empenhado ?? 0),
    totalLiquidado: Number(result.total_liquidado ?? 0),
    totalPago: Number(result.total_pago ?? 0),
    servidoresEfetivos: Number(result.servidores_efetivos ?? 0),
    servidoresTemporarios: Number(result.servidores_temporarios ?? 0),
  } satisfies HistoriaCapremMetricsDTO;
}

export interface EntityCapremDTO {
  entidade: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  taxaExecucao: number;
}

export async function getCapremEntidadesMetrics(
  portalSlug: string,
  ano: number,
): Promise<EntityCapremDTO[]> {
  try {
    const rows = await db
      .selectFrom("fct_caprem_entidades_metricas")
      .select(["entidade", "empenhado", "liquidado", "pago", "taxa_execucao"])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .orderBy("empenhado", "desc")
      .execute();

    return rows.map((r) => ({
      entidade: r.entidade ?? "",
      empenhado: Number(r.empenhado ?? 0),
      liquidado: Number(r.liquidado ?? 0),
      pago: Number(r.pago ?? 0),
      taxaExecucao: Number(r.taxa_execucao ?? 0),
    }));
  } catch {
    return [];
  }
}

export interface CapremNaturezaMetricDTO {
  elemento: string;
  descricao: string;
  destino: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  dataEmpenho?: string;
}

export async function getCapremNaturezaMetrics(
  portalSlug: string,
  ano: number,
): Promise<CapremNaturezaMetricDTO[]> {
  try {
    const rows = await db
      .selectFrom("fct_caprem_natureza_metricas")
      .select([
        "elemento",
        "natureza_despesa as naturezaDespesa",
        "destino",
        "descricao",
        "data_empenho as dataEmpenho",
        "empenhado",
        "liquidado",
        "pago",
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .orderBy("empenhado", "desc")
      .execute();

    if (rows.length > 0) {
      return rows.map((r) => {
        let cleanDate: string | undefined;
        if (r.dataEmpenho) {
          cleanDate =
            r.dataEmpenho instanceof Date
              ? r.dataEmpenho.toISOString().split("T")[0]
              : String(r.dataEmpenho).split("T")[0];
        }
        return {
          elemento: r.elemento ?? "",
          descricao:
            r.naturezaDespesa ||
            (r.elemento ? `Elemento ${r.elemento}` : "Despesa Previdenciária"),
          destino: r.destino ?? "encargo_patronal_geral",
          empenhado: Number(r.empenhado ?? 0),
          liquidado: Number(r.liquidado ?? 0),
          pago: Number(r.pago ?? 0),
          dataEmpenho: cleanDate,
        };
      });
    }
  } catch {
    // Fallback para fct_despesas caso a tabela fct_caprem_natureza_metricas ainda não tenha sido criada via dbt run
  }

  try {
    const rows = await db
      .selectFrom("fct_despesas as d")
      .leftJoin(
        "dim_elemento_despesa as dim",
        "d.elemento",
        "dim.elemento_codigo",
      )
      .select([
        "d.empenho_id as empenhoId",
        "d.elemento",
        sql<string>`coalesce(dim.elemento_descricao, d.natureza_despesa, '')`.as(
          "naturezaDespesa",
        ),
        "d.fornecedor_nome as fornecedorNome",
        "d.descricao",
        "d.data_empenho as dataEmpenho",
        sql<number>`cast(coalesce(sum(d.empenhado_liquido), 0) as numeric)`.as(
          "empenhado",
        ),
        sql<number>`cast(coalesce(sum(d.liquidado), 0) as numeric)`.as(
          "liquidado",
        ),
        sql<number>`cast(coalesce(sum(d.pago), 0) as numeric)`.as("pago"),
      ])
      .where("d.portal_slug", "=", portalSlug)
      .where("d.ano", "=", ano)
      .where((eb) =>
        eb.or([
          eb("d.elemento", "in", ["13", "71", "97"]),
          eb("d.orgao_codigo", "=", "1061"),
          eb("d.credor_id", "=", "1061"),
          eb("d.fornecedor_nome", "ilike", "%CAPREM%"),
          eb("d.fornecedor_nome", "ilike", "%CASP%"),
          eb("d.fornecedor_cpf_cnpj", "=", "07.573.075/0001-00"),
          eb("d.descricao", "ilike", "%CAPREM%"),
          eb("d.descricao", "ilike", "%CASP%"),
        ]),
      )
      .where((eb) =>
        eb.or([
          eb("d.tipo_empenho", "is", null),
          eb("d.tipo_empenho", "!=", "AN"),
        ]),
      )
      .groupBy([
        "d.empenho_id",
        "d.elemento",
        "dim.elemento_descricao",
        "d.natureza_despesa",
        "d.fornecedor_nome",
        "d.descricao",
        "d.data_empenho",
      ])
      .orderBy("empenhado", "desc")
      .execute();

    return rows.map((r) => {
      const elemento = r.elemento ?? "";
      const fornecedor = r.fornecedorNome ?? "";
      const descText = r.descricao ?? "";
      const naturezaDesc =
        r.naturezaDespesa ||
        (elemento ? `Elemento ${elemento}` : "Despesa Previdenciária");
      let destino = "encargo_patronal_geral";

      if (
        fornecedor.toLowerCase().includes("casp") ||
        descText.toLowerCase().includes("casp") ||
        naturezaDesc.toLowerCase().includes("casp")
      ) {
        destino = "plano_saude_casp";
      } else if (elemento === "97") {
        destino = "aporte_atuarial_caprem";
      } else if (elemento === "71") {
        destino = "amortizacao_divida_caprem";
      } else if (
        naturezaDesc.toLowerCase().includes("inss") ||
        naturezaDesc.toLowerCase().includes("rgps")
      ) {
        destino = "inss_rgps";
      } else if (
        elemento === "13" ||
        fornecedor.toLowerCase().includes("caprem") ||
        descText.toLowerCase().includes("caprem")
      ) {
        destino = "rpps_caprem";
      }

      let cleanDate: string | undefined;
      if (r.dataEmpenho) {
        cleanDate =
          r.dataEmpenho instanceof Date
            ? r.dataEmpenho.toISOString().split("T")[0]
            : String(r.dataEmpenho).split("T")[0];
      }

      return {
        elemento,
        descricao: naturezaDesc,
        destino,
        empenhado: Number(r.empenhado ?? 0),
        liquidado: Number(r.liquidado ?? 0),
        pago: Number(r.pago ?? 0),
        dataEmpenho: cleanDate,
      };
    });
  } catch {
    return [];
  }
}

export interface CapremActuarialTrendDTO {
  ano: number;
  aporteExigido: number;
  aporteQuitado: number;
  taxaAdimplencia: number;
  amortizacaoDivida: number;
}

export async function getCapremActuarialTrendMetrics(
  portalSlug: string,
): Promise<CapremActuarialTrendDTO[]> {
  try {
    const rows = await db
      .selectFrom("fct_caprem_tendencia_atuarial_metricas")
      .select([
        "ano",
        "aporte_exigido as aporteExigido",
        "aporte_quitado as aporteQuitado",
        "taxa_adimplencia as taxaAdimplencia",
        "amortizacao_divida as amortizacaoDivida",
      ])
      .where("portal_slug", "=", portalSlug)
      .orderBy("ano", "asc")
      .execute();

    if (rows.length > 0) {
      return rows.map((r) => ({
        ano: Number(r.ano),
        aporteExigido: Number(r.aporteExigido ?? 0),
        aporteQuitado: Number(r.aporteQuitado ?? 0),
        taxaAdimplencia: Number(r.taxaAdimplencia ?? 0),
        amortizacaoDivida: Number(r.amortizacaoDivida ?? 0),
      }));
    }
  } catch {
    // Fallback para fct_despesas caso a tabela ainda não exista no DB
  }

  try {
    const rows = await db
      .selectFrom("fct_despesas")
      .select([
        "ano",
        sql<number>`cast(coalesce(sum(case when elemento = '97' then empenhado_liquido else 0 end), 0) as numeric)`.as(
          "aporte_exigido",
        ),
        sql<number>`cast(coalesce(sum(case when elemento = '97' then pago else 0 end), 0) as numeric)`.as(
          "aporte_quitado",
        ),
        sql<number>`cast(coalesce(sum(case when elemento = '71' then pago else 0 end), 0) as numeric)`.as(
          "amortizacao_divida",
        ),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", ">=", 2021)
      .where("elemento", "in", ["97", "71"])
      .where((eb) =>
        eb.or([eb("tipo_empenho", "is", null), eb("tipo_empenho", "!=", "AN")]),
      )
      .groupBy("ano")
      .orderBy("ano", "asc")
      .execute();

    return rows.map((r) => {
      const exigido = Number(r.aporte_exigido ?? 0);
      const quitado = Number(r.aporte_quitado ?? 0);
      return {
        ano: Number(r.ano),
        aporteExigido: exigido,
        aporteQuitado: quitado,
        taxaAdimplencia: exigido > 0 ? (quitado / exigido) * 100 : 100,
        amortizacaoDivida: Number(r.amortizacao_divida ?? 0),
      };
    });
  } catch {
    return [];
  }
}

export interface CadprevParcelamentoItemDTO {
  numeroCadprev: string;
  descricao: string;
  elemento: string;
  empenhado: number;
  pago: number;
  dataEmpenho?: string;
}

export async function getCapremCadprevMetrics(
  portalSlug: string,
  ano: number,
): Promise<CadprevParcelamentoItemDTO[]> {
  try {
    const rows = await db
      .selectFrom("fct_despesas")
      .select([
        "empenho_id as empenhoId",
        "descricao",
        "elemento",
        "data_empenho",
        sql<number>`cast(coalesce(sum(empenhado_liquido), 0) as numeric)`.as(
          "empenhado",
        ),
        sql<number>`cast(coalesce(sum(pago), 0) as numeric)`.as("pago"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where("elemento", "=", "71")
      .where((eb) =>
        eb.or([eb("tipo_empenho", "is", null), eb("tipo_empenho", "!=", "AN")]),
      )
      .groupBy(["empenho_id", "descricao", "elemento", "data_empenho"])
      .orderBy("empenhado", "desc")
      .execute();

    return rows.map((r) => {
      const match = r.descricao
        ? r.descricao.match(/CADPREV\s*(?:N[º°]?\s*)?([\d/]+)/i)
        : null;
      const cadprevStr = match
        ? `CADPREV Nº ${match[1]}`
        : r.empenhoId
          ? `Empenho ${r.empenhoId}`
          : "N/A";
      let cleanDate: string | undefined;
      if (r.data_empenho) {
        cleanDate = String(r.data_empenho).split("T")[0];
      }
      return {
        numeroCadprev: cadprevStr,
        descricao:
          r.descricao ?? "Parcelamento de Dívida Previdenciária (Elemento 71)",
        elemento: r.elemento ?? "71",
        empenhado: Number(r.empenhado ?? 0),
        pago: Number(r.pago ?? 0),
        dataEmpenho: cleanDate,
      };
    });
  } catch {
    return [];
  }
}
