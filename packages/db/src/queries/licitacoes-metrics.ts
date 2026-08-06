import { db } from "../client";
import { dispensationThreshold, NEAR_THRESHOLD_PCT } from "../constants";
import { SAUDE_EMPRESA } from "./licitacao_gaps";

export interface ContratoSemLicitacaoMetricsDTO {
  ano: number;
  empresa: string;
  numero: string;
  fornecedor: string;
  objeto: string;
  valorContrato: string;
  licitacaoNumero: string;
  mes: number;
  numeroObra: string | null;
  tipoObra: string | null;
  modalidade: string | null;
  fundlegal: string | null;
  limiteDispensa: number;
  acimaLimite: boolean;
  orgaoSaude: boolean;
  periodo: string;
  isentoLegalmente?: boolean;
}

export interface ItemDistribucaoModalidadeMetricsDTO {
  modalidade: string;
  valorTotal: number;
  quantidade: number;
  percentual_valor: number;
  pctValor: number;
}

export interface ItemAdesaoAtaMetricsDTO {
  numero: string;
  objeto: string;
  licitacaoValor: number;
  carona: string;
  totalValorContrato: number;
  totalEmpenhadoContrato: number;
  total_contrato_valor: number;
  total_contrato_empenhado: number;
  totalCValor: number;
  totalCEmpenhado: number;
  mes: number | null;
  temContrato: boolean;
  periodo: string;
}

export interface AdesaoAtaResultMetricsDTO {
  lista: ItemAdesaoAtaMetricsDTO[];
  quantidade: number;
  valor: number;
  totalLicitacao: number;
  contratosAssociadosCount: number;
}

export interface ItemAdesaoExternaMetricsDTO {
  data: string;
  fornecedor: string;
  empenhado: number;
  pago: number;
  unidade: string;
  justificativa: string;
  numLicitacao: string;
}

export interface AdesaoExternaResultMetricsDTO {
  lista: ItemAdesaoExternaMetricsDTO[];
  quantidade: number;
  totalPago: number;
}

export interface ContratoFracionamentoMetricsDTO {
  ano: number;
  empresa: string;
  numero: string;
  fornecedor: string;
  objeto: string;
  valorContrato: number;
  licitacaoNumero: string;
  mes: number;
  periodo: string;
  Periodo: string;
}

export interface FornecedorRecorrenteMetricsDTO {
  empresa: string;
  fornecedor: string;
  quantidade: number;
  total: number;
  percentual: number;
  pct: number;
}

export interface AnomaliasResultMetricsDTO {
  fracionamento: ContratoFracionamentoMetricsDTO[];
  fornecedorRecorrente: FornecedorRecorrenteMetricsDTO[];
  janelaCurta: ContratoSemLicitacaoMetricsDTO[];
}

/**
 * Retorna os contratos sem licitação (gaps) a partir do mart unificado `fct_licitacoes_metricas`.
 */
export async function getLicitacaoGapsMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<ContratoSemLicitacaoMetricsDTO[]> {
  if (!portalSlug || Number.isNaN(year)) return [];
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return [];

  let query = db
    .selectFrom("fct_licitacoes_metricas")
    .select([
      "ano",
      "empresa_id as empresa",
      "contrato_numero as numero",
      "fornecedor_nome as fornecedor",
      "objeto",
      "valor_contrato",
      "licitacao_numero",
      "mes",
      "numero_obra",
      "tipo_obra",
      "modalidade",
      "fundlegal",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year)
    .where("tipo_contratacao", "=", "gap_licitacao");

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const rows = await query.execute();

  return rows.map((r) => {
    const empresa = String(r.empresa ?? "");
    const valor_contrato = parseFloat(String(r.valor_contrato ?? "0")) || 0;
    const limite_dispensa = dispensationThreshold(
      r.numero_obra,
      r.tipo_obra,
      r.objeto,
    );
    const mes_num =
      r.mes !== null && r.mes !== undefined && !Number.isNaN(Number(r.mes))
        ? Number(r.mes)
        : 0;
    const mes_str = mes_num > 0 ? String(mes_num).padStart(2, "0") : "00";

    return {
      ano: Number(r.ano),
      empresa,
      numero: String(r.numero ?? ""),
      fornecedor: String(r.fornecedor ?? ""),
      objeto: String(r.objeto ?? ""),
      valorContrato: String(r.valor_contrato ?? "0"),
      licitacaoNumero: String(r.licitacao_numero ?? ""),
      mes: mes_num,
      numeroObra: r.numero_obra ?? null,
      tipoObra: r.tipo_obra ?? null,
      modalidade: r.modalidade ?? null,
      fundlegal: r.fundlegal ?? null,
      limiteDispensa: limite_dispensa,
      acimaLimite: valor_contrato > limite_dispensa,
      orgaoSaude: empresa === SAUDE_EMPRESA,
      periodo: `${mes_str}/${r.ano}`,
    };
  });
}

/**
 * Retorna a distribuição por modalidades de licitação a partir do mart `fct_licitacoes_modalidades_metricas`.
 */
export async function getDistribucaoModalidadesMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<ItemDistribucaoModalidadeMetricsDTO[]> {
  if (!portalSlug || Number.isNaN(year)) return [];
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return [];

  let query = db
    .selectFrom("fct_licitacoes_modalidades_metricas")
    .select([
      "modalidade",
      db.fn.sum<string>("quantidade").as("quantidade"),
      db.fn.sum<string>("valor_total").as("valor_total"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year);

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const rows = await query
    .groupBy("modalidade")
    .orderBy("valor_total", "desc")
    .execute();

  const total_geral = rows.reduce(
    (acc, r) => acc + (parseFloat(String(r.valor_total ?? "0")) || 0),
    0,
  );

  return rows.map((r) => {
    const valor_total = parseFloat(String(r.valor_total ?? "0")) || 0;
    const percentual_valor =
      total_geral > 0 ? (valor_total / total_geral) * 100 : 0;
    const modalidade = String(r.modalidade ?? "outros").toLowerCase();
    return {
      modalidade,
      valorTotal: valor_total,
      quantidade: Number(r.quantidade ?? 0),
      percentual_valor,
      pctValor: percentual_valor,
    };
  });
}

/**
 * Retorna adesaos de ata (caronas) a partir do mart unificado `fct_licitacoes_metricas`.
 */
export async function getAdesaoDeAtaMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<AdesaoAtaResultMetricsDTO> {
  const emptyResult: AdesaoAtaResultMetricsDTO = {
    lista: [],
    quantidade: 0,
    valor: 0,
    totalLicitacao: 0,
    contratosAssociadosCount: 0,
  };

  if (!portalSlug || Number.isNaN(year)) return emptyResult;
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return emptyResult;

  let query = db
    .selectFrom("fct_licitacoes_metricas")
    .select([
      "numero",
      "objeto",
      "licitacao_valor",
      "carona",
      "mes",
      "valor_contrato",
      "empenhado_contrato",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year)
    .where("tipo_contratacao", "=", "adesao_ata_interna");

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const rows = await query.execute();
  if (rows.length === 0) return emptyResult;

  const groupedMap = new Map<
    string,
    {
      numero: string;
      objeto: string;
      licitacaoValor: number;
      carona: string;
      totalValorContrato: number;
      totalEmpenhadoContrato: number;
      mes: number | null;
    }
  >();

  for (const r of rows) {
    const key = `${r.numero ?? ""}__${r.objeto ?? ""}`;
    const licitacao_valor = parseFloat(String(r.licitacao_valor ?? "0")) || 0;
    const contrato_valor = parseFloat(String(r.valor_contrato ?? "0")) || 0;
    const contrato_empenhado =
      parseFloat(String(r.empenhado_contrato ?? "0")) || 0;
    const mes_num =
      r.mes !== null && r.mes !== undefined && !Number.isNaN(Number(r.mes))
        ? Number(r.mes)
        : null;

    const existing = groupedMap.get(key);
    if (existing) {
      existing.totalValorContrato += contrato_valor;
      existing.totalEmpenhadoContrato += contrato_empenhado;
      if (existing.mes === null) existing.mes = mes_num;
    } else {
      groupedMap.set(key, {
        numero: String(r.numero ?? ""),
        objeto: String(r.objeto ?? ""),
        licitacaoValor: licitacao_valor,
        carona: String(r.carona ?? "S"),
        totalValorContrato: contrato_valor,
        totalEmpenhadoContrato: contrato_empenhado,
        mes: mes_num,
      });
    }
  }

  const lista: ItemAdesaoAtaMetricsDTO[] = Array.from(groupedMap.values()).map(
    (item) => {
      const mes_str = item.mes ? String(item.mes).padStart(2, "0") : "";
      return {
        ...item,
        total_contrato_valor: item.totalValorContrato,
        total_contrato_empenhado: item.totalEmpenhadoContrato,
        totalCValor: item.totalValorContrato,
        totalCEmpenhado: item.totalEmpenhadoContrato,
        temContrato: item.totalValorContrato > 0,
        periodo: mes_str ? `${mes_str}/${year}` : "",
      };
    },
  );

  return {
    lista,
    quantidade: lista.length,
    valor: lista.reduce((acc, i) => acc + i.totalValorContrato, 0),
    totalLicitacao: lista.reduce((acc, i) => acc + i.licitacaoValor, 0),
    contratosAssociadosCount: lista.filter((i) => i.temContrato).length,
  };
}

/**
 * Retorna adesaos externas a partir do mart unificado `fct_licitacoes_metricas`.
 */
export async function getAdesaoExternaMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<AdesaoExternaResultMetricsDTO> {
  const emptyResult: AdesaoExternaResultMetricsDTO = {
    lista: [],
    quantidade: 0,
    totalPago: 0,
  };

  if (!portalSlug || Number.isNaN(year)) return emptyResult;
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return emptyResult;

  let query = db
    .selectFrom("fct_licitacoes_metricas")
    .select([
      "data_referencia as data",
      "fornecedor_nome as fornecedor",
      "empenhado_contrato as empenhado",
      "pago_contrato as pago",
      "empresa_id as unidade",
      "objeto as justificativa",
      "licitacao_numero as num_licitacao",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year)
    .where("tipo_contratacao", "=", "adesao_ata_externa");

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const rows = await query.orderBy("pago_contrato", "desc").execute();

  const lista: ItemAdesaoExternaMetricsDTO[] = rows.map((r) => ({
    data: r.data ? String(r.data) : "",
    fornecedor: String(r.fornecedor ?? ""),
    empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
    pago: parseFloat(String(r.pago ?? "0")) || 0,
    unidade: String(r.unidade ?? ""),
    justificativa: String(r.justificativa ?? ""),
    numLicitacao: String(r.num_licitacao ?? ""),
  }));

  return {
    lista,
    quantidade: lista.length,
    totalPago: lista.reduce((acc, i) => acc + i.pago, 0),
  };
}

/**
 * Retorna anomalias contratuais a partir do mart unificado `fct_licitacoes_metricas`.
 */
export async function getAnomaliasContratuaisMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<AnomaliasResultMetricsDTO> {
  const emptyAnomalias: AnomaliasResultMetricsDTO = {
    fracionamento: [],
    fornecedorRecorrente: [],
    janelaCurta: [],
  };

  if (!portalSlug || Number.isNaN(year)) return emptyAnomalias;
  if (Array.isArray(empresaIds) && empresaIds.length === 0)
    return emptyAnomalias;

  let gapQuery = db
    .selectFrom("fct_licitacoes_metricas")
    .select([
      "ano",
      "empresa_id as empresa",
      "contrato_numero as numero",
      "fornecedor_nome as fornecedor",
      "objeto",
      "valor_contrato",
      "licitacao_numero",
      "mes",
      "numero_obra",
      "tipo_obra",
      "modalidade",
      "fundlegal",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year)
    .where("tipo_contratacao", "=", "gap_licitacao");

  let totalContratosQuery = db
    .selectFrom("fct_licitacoes_metricas")
    .select(["empresa_id as empresa", db.fn.countAll().as("total_contratos")])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year);

  if (empresaIds && empresaIds.length > 0) {
    gapQuery = gapQuery.where("empresa_id", "in", empresaIds);
    totalContratosQuery = totalContratosQuery.where(
      "empresa_id",
      "in",
      empresaIds,
    );
  }

  const [contratos, totalContratosRows] = await Promise.all([
    gapQuery.execute(),
    totalContratosQuery.groupBy("empresa_id").execute(),
  ]);

  const totalContratosMap = new Map<string, number>(
    totalContratosRows.map((r) => [
      String(r.empresa ?? ""),
      Number(r.total_contratos ?? 0),
    ]),
  );

  const proximo = contratos
    .map((c) => {
      const valor = parseFloat(String(c.valor_contrato ?? "0")) || 0;
      const limite = dispensationThreshold(
        c.numero_obra,
        c.tipo_obra,
        c.objeto,
      );
      const limite_inferior = limite * (1 - NEAR_THRESHOLD_PCT);
      return {
        ...c,
        valorNum: valor,
        isProximo: valor >= limite_inferior && valor < limite,
      };
    })
    .filter((c) => c.isProximo);

  const countFrac = new Map<string, number>();
  for (const p of proximo) {
    const key = `${p.empresa ?? ""}__${p.fornecedor ?? ""}`;
    countFrac.set(key, (countFrac.get(key) || 0) + 1);
  }

  const chavesFrac = new Set<string>();
  for (const [k, cnt] of countFrac.entries()) {
    if (cnt >= 3) chavesFrac.add(k);
  }

  const fracionamento: ContratoFracionamentoMetricsDTO[] = proximo
    .filter((p) => chavesFrac.has(`${p.empresa ?? ""}__${p.fornecedor ?? ""}`))
    .map((p) => {
      const mes_num =
        p.mes !== null && p.mes !== undefined && !Number.isNaN(Number(p.mes))
          ? Number(p.mes)
          : 0;
      const mes_str = mes_num > 0 ? String(mes_num).padStart(2, "0") : "00";
      const periodo = `${mes_str}/${p.ano}`;
      return {
        ano: Number(p.ano),
        empresa: String(p.empresa ?? ""),
        numero: String(p.numero ?? ""),
        fornecedor: String(p.fornecedor ?? ""),
        objeto: String(p.objeto ?? ""),
        valorContrato: p.valorNum,
        licitacaoNumero: String(p.licitacao_numero ?? ""),
        mes: mes_num,
        periodo,
        Periodo: periodo,
      };
    });

  const empresaFornecedorCount = new Map<string, Map<string, number>>();
  for (const c of contratos) {
    const emp = String(c.empresa ?? "");
    const forn = String(c.fornecedor ?? "");
    let fornMap = empresaFornecedorCount.get(emp);
    if (!fornMap) {
      fornMap = new Map<string, number>();
      empresaFornecedorCount.set(emp, fornMap);
    }
    fornMap.set(forn, (fornMap.get(forn) || 0) + 1);
  }

  const fornecedorRecorrente: FornecedorRecorrenteMetricsDTO[] = [];
  for (const [emp, mapForn] of empresaFornecedorCount.entries()) {
    const total_contratos = totalContratosMap.get(emp) || 0;
    if (total_contratos === 0) continue;
    for (const [forn, qtd] of mapForn.entries()) {
      const percentual = qtd / total_contratos;
      if (percentual > 0.5) {
        fornecedorRecorrente.push({
          empresa: emp,
          fornecedor: forn,
          quantidade: qtd,
          total: total_contratos,
          percentual,
          pct: percentual,
        });
      }
    }
  }

  return {
    fracionamento,
    fornecedorRecorrente,
    janelaCurta: [],
  };
}
