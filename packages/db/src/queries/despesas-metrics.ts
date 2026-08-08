import { db } from "../client";

export interface ResumoDiariasMetricsDTO {
  totalValor: number;
  totalViajantes: number;
  mediaReembolso: number;
}

export interface BeneficiarioDiariaMetricsDTO {
  favorecido: string;
  nome: string;
  cargo: string;
  quantidade: number;
  valor: number;
  total: number;
}

export interface ImpactoGastosLocaisMetricsDTO {
  localPago: number;
  externoPago: number;
  totalPago: number;
  pctLocal: number;
  historicoLocalPago: number;
  historicoExternoPago: number;
  historicoTotalPago: number;
  historicoPctLocal: number;
}

export interface ItemFornecedorTopMetrics {
  codigo: string;
  descricao: string;
  empenhado: number;
  percentual: number;
}

export interface ConcentracaoFornecedoresMetricsDTO {
  top10: ItemFornecedorTopMetrics[];
  hhi: number;
  dominante: string | null;
  totalAll: number;
}

export interface RestosAPagarResumoMetricsDTO {
  restosInscritos: number;
  restosPagos: number;
  restosCancelados: number;
  saldoRestos: number;
  totalPendente: number;
  fornecedoresAguardando: number;
  dividaMaisAntigaAno: number;
  topFornecedores: Array<{ fornecedor: string; valor: number }>;
}

export interface DespesaUnidadeMetricsDTO {
  descricao: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  dotacaoAtualizada: number;
}

export async function getResumoDiariasMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<ResumoDiariasMetricsDTO> {
  if (empresaIds.length === 0) {
    return { totalValor: 0, totalViajantes: 0, mediaReembolso: 0 };
  }

  try {
    const totals = await db
      .selectFrom("fct_despesas_diarias_metricas")
      .select((eb) => [
        eb.fn.sum<string>("total_valor").as("total_valor"),
        eb.fn.sum<string>("qtd_concessoes").as("qtd_concessoes"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where("empresa_id", "in", empresaIds)
      .where("favorecido", "=", "__TOTAL__")
      .executeTakeFirst();

    const viajantesRes = await db
      .selectFrom("fct_despesas_diarias_metricas")
      .select("favorecido")
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano)
      .where("empresa_id", "in", empresaIds)
      .where("favorecido", "!=", "__TOTAL__")
      .groupBy("favorecido")
      .execute();

    const totalValor = Number(totals?.total_valor ?? 0);
    const qtdConcessoes = Number(totals?.qtd_concessoes ?? 0);
    const totalViajantes = viajantesRes.length;

    return {
      totalValor,
      totalViajantes,
      mediaReembolso: qtdConcessoes > 0 ? totalValor / qtdConcessoes : 0,
    };
  } catch {
    return { totalValor: 0, totalViajantes: 0, mediaReembolso: 0 };
  }
}

export async function getPrincipaisBeneficiariosDiariasMetrics({
  portalSlug,
  year,
  limit = 10,
  empresaIds,
}: {
  portalSlug: string;
  year: number;
  limit?: number;
  empresaIds: string[];
}): Promise<BeneficiarioDiariaMetricsDTO[]> {
  if (empresaIds.length === 0) return [];

  try {
    const results = await db
      .selectFrom("fct_despesas_diarias_metricas")
      .select((eb) => [
        "favorecido",
        "cargo",
        eb.fn.sum<string>("total_valor").as("total"),
        eb.fn.sum<string>("qtd_concessoes").as("quantidade"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", year)
      .where("empresa_id", "in", empresaIds)
      .where("favorecido", "!=", "__TOTAL__")
      .groupBy(["favorecido", "cargo"])
      .orderBy("total", "desc")
      .limit(limit)
      .execute();

    return results.map((r) => {
      const tot = Number(r.total ?? 0);
      const fav = r.favorecido ?? "";
      return {
        favorecido: fav,
        nome: fav,
        cargo: r.cargo ?? "",
        quantidade: Number(r.quantidade ?? 0),
        valor: tot,
        total: tot,
      };
    });
  } catch {
    return [];
  }
}

export async function getImpactoGastosLocaisMetrics({
  portalSlug,
  year,
  empresaIds,
  cidadeClean,
}: {
  portalSlug: string;
  year: number;
  empresaIds: string[];
  cidadeClean: string;
}): Promise<ImpactoGastosLocaisMetricsDTO> {
  const emptyResult: ImpactoGastosLocaisMetricsDTO = {
    localPago: 0,
    externoPago: 0,
    totalPago: 0,
    pctLocal: 0,
    historicoLocalPago: 0,
    historicoExternoPago: 0,
    historicoTotalPago: 0,
    historicoPctLocal: 0,
  };

  if (empresaIds.length === 0) return emptyResult;

  try {
    const normalizedCidade = cidadeClean.trim().toUpperCase();

    const currentYearRows = await db
      .selectFrom("fct_despesas_fornecedores_metricas")
      .select((eb) => [
        "fornecedor_cidade_clean",
        eb.fn.sum<string>("total_pago").as("total_pago"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", year)
      .where("empresa_id", "in", empresaIds)
      .groupBy("fornecedor_cidade_clean")
      .execute();

    let localPago = 0;
    let externoPago = 0;

    for (const r of currentYearRows) {
      const val = Number(r.total_pago ?? 0);
      if (
        r.fornecedor_cidade_clean === normalizedCidade ||
        (normalizedCidade === "PORCIUNCULA" && !r.fornecedor_cidade_clean)
      ) {
        localPago += val;
      } else {
        externoPago += val;
      }
    }

    const totalPago = localPago + externoPago;
    const pctLocal = totalPago > 0 ? (localPago / totalPago) * 100 : 0;

    const histRows = await db
      .selectFrom("fct_despesas_fornecedores_metricas")
      .select((eb) => [
        "fornecedor_cidade_clean",
        eb.fn.sum<string>("total_pago").as("total_pago"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "<", year)
      .where("empresa_id", "in", empresaIds)
      .groupBy("fornecedor_cidade_clean")
      .execute();

    let historicoLocalPago = 0;
    let historicoExternoPago = 0;

    for (const r of histRows) {
      const val = Number(r.total_pago ?? 0);
      if (
        r.fornecedor_cidade_clean === normalizedCidade ||
        (normalizedCidade === "PORCIUNCULA" && !r.fornecedor_cidade_clean)
      ) {
        historicoLocalPago += val;
      } else {
        historicoExternoPago += val;
      }
    }

    const historicoTotalPago = historicoLocalPago + historicoExternoPago;
    const historicoPctLocal =
      historicoTotalPago > 0
        ? (historicoLocalPago / historicoTotalPago) * 100
        : 0;

    return {
      localPago,
      externoPago,
      totalPago,
      pctLocal,
      historicoLocalPago,
      historicoExternoPago,
      historicoTotalPago,
      historicoPctLocal,
    };
  } catch {
    return emptyResult;
  }
}

export async function getConcentracaoFornecedoresMetrics(
  portalSlug: string,
  year: number,
  empresaIds: string[],
): Promise<ConcentracaoFornecedoresMetricsDTO> {
  const emptyResult: ConcentracaoFornecedoresMetricsDTO = {
    top10: [],
    hhi: 0,
    dominante: null,
    totalAll: 0,
  };

  if (empresaIds.length === 0) return emptyResult;

  try {
    const rows = await db
      .selectFrom("fct_despesas_fornecedores_metricas")
      .select((eb) => [
        "fornecedor_codigo",
        "fornecedor_nome",
        eb.fn.sum<string>("total_empenhado").as("empenhado"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", year)
      .where("empresa_id", "in", empresaIds)
      .groupBy(["fornecedor_codigo", "fornecedor_nome"])
      .orderBy("empenhado", "desc")
      .execute();

    let totalAll = 0;
    const items = rows.map((r) => {
      const emp = Number(r.empenhado ?? 0);
      totalAll += emp;
      return {
        codigo: r.fornecedor_codigo,
        descricao: r.fornecedor_nome,
        empenhado: emp,
        percentual: 0,
      };
    });

    const formattedItems = items.map((i) => ({
      ...i,
      percentual: totalAll > 0 ? (i.empenhado / totalAll) * 100 : 0,
    }));

    const top10 = formattedItems.slice(0, 10);

    const sumHHI = formattedItems.reduce((acc, i) => {
      const share = totalAll > 0 ? i.empenhado / totalAll : 0;
      return acc + share * share;
    }, 0);
    const hhi = sumHHI * 10000;

    const domItem = formattedItems.find((i) => i.percentual > 40);
    const dominante = domItem ? domItem.descricao : null;

    return { top10, hhi, dominante, totalAll };
  } catch {
    return emptyResult;
  }
}

export async function getRestosAPagarResumoMetrics(
  portalSlug: string,
  year: number,
  empresaIds: string[],
): Promise<RestosAPagarResumoMetricsDTO> {
  const emptyResult: RestosAPagarResumoMetricsDTO = {
    restosInscritos: 0,
    restosPagos: 0,
    restosCancelados: 0,
    saldoRestos: 0,
    totalPendente: 0,
    fornecedoresAguardando: 0,
    dividaMaisAntigaAno: year,
    topFornecedores: [],
  };

  if (empresaIds.length === 0) return emptyResult;

  try {
    const result = await db
      .selectFrom("fct_despesas_restos_metricas")
      .select((eb) => [
        eb.fn.sum<string>("restos_inscritos").as("restos_inscritos"),
        eb.fn.sum<string>("restos_pagos").as("restos_pagos"),
        eb.fn.sum<string>("restos_cancelados").as("restos_cancelados"),
        eb.fn.sum<string>("saldo_restos").as("saldo_restos"),
        eb.fn
          .min<number>("divida_mais_antiga_ano")
          .as("divida_mais_antiga_ano"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", year)
      .where("empresa_id", "in", empresaIds)
      .executeTakeFirst();

    const rows = await db
      .selectFrom("fct_despesas")
      .select(["ano", "fornecedor_nome", "descricao", "empenhado", "pago"])
      .where("portal_slug", "=", portalSlug)
      .where("fonte", "=", "restos_a_pagar")
      .where("ano", "=", year)
      .where("empresa_id", "in", empresaIds)
      .execute();

    let totalPendente = 0;
    let dividaMaisAntigaAno = Number(result?.divida_mais_antiga_ano ?? year);
    const fornecedoresSet = new Set<string>();
    const mapFornecedores: Record<string, number> = {};

    for (const r of rows) {
      const emp = Number(r.empenhado ?? 0);
      const pag = Number(r.pago ?? 0);
      const pend = emp - pag;
      if (pend > 0) {
        totalPendente += pend;
        const a = Number(r.ano);
        if (a > 0 && a < dividaMaisAntigaAno) {
          dividaMaisAntigaAno = a;
        }
        const nome = String(
          r.fornecedor_nome || r.descricao || "Não identificado",
        ).trim();
        fornecedoresSet.add(nome);
        mapFornecedores[nome] = (mapFornecedores[nome] || 0) + pend;
      }
    }

    const restosInscritos = Number(result?.restos_inscritos ?? 0);
    const restosPagos = Number(result?.restos_pagos ?? 0);
    const restosCancelados = Number(result?.restos_cancelados ?? 0);
    const saldoRestos = Number(result?.saldo_restos ?? 0);

    const topFornecedores = Object.entries(mapFornecedores)
      .map(([fornecedor, valor]) => ({ fornecedor, valor }))
      .sort((a, b) => b.valor - a.valor)
      .slice(0, 5);

    return {
      restosInscritos,
      restosPagos,
      restosCancelados,
      saldoRestos,
      totalPendente: totalPendente > 0 ? totalPendente : saldoRestos,
      fornecedoresAguardando: fornecedoresSet.size,
      dividaMaisAntigaAno,
      topFornecedores,
    };
  } catch {
    return emptyResult;
  }
}

export async function getDespesasPorUnidadeMetrics(
  portalSlug: string,
  year: number,
  empresaIds: string[],
): Promise<DespesaUnidadeMetricsDTO[]> {
  if (empresaIds.length === 0) return [];

  try {
    const results = await db
      .selectFrom("fct_despesas_por_unidade")
      .select((eb) => [
        "descricao",
        eb.fn.sum<string>("empenhado").as("empenhado"),
        eb.fn.sum<string>("liquidado").as("liquidado"),
        eb.fn.sum<string>("pago").as("pago"),
        eb.fn.sum<string>("dotacao_atualizada").as("dotacao_atualizada"),
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", year)
      .where("empresa", "in", empresaIds)
      .groupBy("descricao")
      .orderBy("empenhado", "desc")
      .execute();

    return results.map((r) => ({
      descricao: String(r.descricao ?? ""),
      empenhado: Number(r.empenhado ?? 0),
      liquidado: Number(r.liquidado ?? 0),
      pago: Number(r.pago ?? 0),
      dotacaoAtualizada: Number(r.dotacao_atualizada ?? 0),
    }));
  } catch {
    return [];
  }
}
