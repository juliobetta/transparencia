import { db } from "../client";
import { getFontesReceitaMetrics } from "./fontes-receita-metrics";

export interface FolhaVsServicosMetricsDTO {
  ano: number;
  totalFolha: number;
  totalPago: number;
  rclProxy: number;
  percentualFolha: number;
}

export interface DecimoTerceiroExecucaoMetricsDTO {
  empenhado: number;
  empenhadoBruto: number;
  liquidado: number;
  pago: number;
  percentual_pago: number;
  pctPago: number;
}

export interface SalaryBinMetricsDTO {
  faixa: string;
  min: number;
  max: number;
  count: number;
}

export interface DepartmentalPayrollMetricsDTO {
  descricao: string;
  pago: number;
}

/**
 * Retorna folha vs serviços (comprometimento da LRF) a partir do mart atômico `fct_pessoal_folha_metricas`.
 */
export async function getFolhaVsServicosMetrics({
  years,
  empresaIds,
  portalSlug,
}: {
  years: number[];
  empresaIds?: string[] | null;
  portalSlug: string;
}): Promise<FolhaVsServicosMetricsDTO[]> {
  if (!portalSlug || !years || years.length === 0) return [];
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return [];

  const validYears = years.filter(
    (y) => typeof y === "number" && !Number.isNaN(y) && y > 1900,
  );
  if (validYears.length === 0) return [];

  let query = db
    .selectFrom("fct_pessoal_folha_metricas")
    .select([
      "ano",
      (eb) => eb.fn.sum<string>("total_folha").as("total_folha"),
      (eb) => eb.fn.sum<string>("total_pago").as("total_pago"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "in", validYears);

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const rows = await query.groupBy("ano").execute();
  const folhaMap = new Map(
    rows.map((r) => [
      Number(r.ano),
      {
        totalFolha: parseFloat(r.total_folha ?? "0") || 0,
        totalPago: parseFloat(r.total_pago ?? "0") || 0,
      },
    ]),
  );

  return Promise.all(
    validYears.map(async (year) => {
      const data = folhaMap.get(year) ?? { totalFolha: 0, totalPago: 0 };
      const fontesReceita = await getFontesReceitaMetrics(
        portalSlug,
        year,
        empresaIds ?? [],
      );
      const rclProxy = fontesReceita ? fontesReceita.totalArrecadado : 0;
      const percentualFolha =
        rclProxy > 0 ? (data.totalFolha / rclProxy) * 100 : 0;

      return {
        ano: year,
        totalFolha: data.totalFolha,
        totalPago: data.totalPago,
        rclProxy,
        percentualFolha,
      };
    }),
  );
}

/**
 * Retorna a execução do 13º salário a partir do mart atômico `fct_pessoal_folha_metricas`.
 */
export async function getExecucaoDecimoTerceiroMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<DecimoTerceiroExecucaoMetricsDTO | null> {
  if (!portalSlug || Number.isNaN(year)) return null;
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return null;

  let query = db
    .selectFrom("fct_pessoal_folha_metricas")
    .select((eb) => [
      eb.fn.sum<string>("empenhado_13").as("empenhado_13"),
      eb.fn.sum<string>("empenhado_bruto_13").as("empenhado_bruto_13"),
      eb.fn.sum<string>("liquidado_13").as("liquidado_13"),
      eb.fn.sum<string>("pago_13").as("pago_13"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year);

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const row = await query.executeTakeFirst();
  if (!row) return null;

  const empenhado_bruto = parseFloat(row.empenhado_bruto_13 ?? "0") || 0;
  const empenhado_liquido =
    parseFloat(row.empenhado_13 ?? "0") || empenhado_bruto;
  const liquidado = parseFloat(row.liquidado_13 ?? "0") || 0;
  const pago = parseFloat(row.pago_13 ?? "0") || 0;

  if (empenhado_bruto === 0 && empenhado_liquido === 0 && pago === 0) {
    return null;
  }

  const percentual_pago = empenhado_liquido > 0 ? pago / empenhado_liquido : 0;

  return {
    empenhado: empenhado_liquido,
    empenhadoBruto: empenhado_bruto,
    liquidado,
    pago,
    percentual_pago,
    pctPago: percentual_pago,
  };
}

/**
 * Retorna o percentual de chefias ocupadas por servidores efetivos a partir de `fct_pessoal_folha_metricas`.
 */
export async function getPercentualChefiasEfetivasMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<number | null> {
  if (!portalSlug || Number.isNaN(year)) return null;
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return null;

  let query = db
    .selectFrom("fct_pessoal_folha_metricas")
    .select((eb) => [
      eb.fn.sum<string>("efetivos_confianca").as("efetivos_confianca"),
      eb.fn.sum<string>("comissionados_externos").as("comissionados_externos"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year);

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const row = await query.executeTakeFirst();
  const efetivos = parseFloat(row?.efetivos_confianca ?? "0") || 0;
  const comissionados = parseFloat(row?.comissionados_externos ?? "0") || 0;
  const total = efetivos + comissionados;

  return total > 0 ? Number(((efetivos / total) * 100).toFixed(1)) : null;
}

/**
 * Retorna a distribuição por faixas salariais (bins de proventos) a partir de `fct_pessoal_folha_metricas`.
 */
export async function getDistribuicaoProventosMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<SalaryBinMetricsDTO[]> {
  if (!portalSlug || Number.isNaN(year)) return [];
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return [];

  let query = db
    .selectFrom("fct_pessoal_folha_metricas")
    .select((eb) => [
      eb.fn.sum<string>("bin_0_25k").as("bin_0_25k"),
      eb.fn.sum<string>("bin_25k_5k").as("bin_25k_5k"),
      eb.fn.sum<string>("bin_5k_75k").as("bin_5k_75k"),
      eb.fn.sum<string>("bin_75k_10k").as("bin_75k_10k"),
      eb.fn.sum<string>("bin_10k_125k").as("bin_10k_125k"),
      eb.fn.sum<string>("bin_125k_15k").as("bin_125k_15k"),
      eb.fn.sum<string>("bin_15k_175k").as("bin_15k_175k"),
      eb.fn.sum<string>("bin_175k_20k").as("bin_175k_20k"),
      eb.fn.sum<string>("bin_acima_20k").as("bin_acima_20k"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year);

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const row = await query.executeTakeFirst();

  const BINS = [
    { faixa: "R$ 0 - 2,5k", min: 0, max: 2500, key: "bin_0_25k" as const },
    { faixa: "R$ 2,5k - 5k", min: 2500, max: 5000, key: "bin_25k_5k" as const },
    { faixa: "R$ 5k - 7,5k", min: 5000, max: 7500, key: "bin_5k_75k" as const },
    {
      faixa: "R$ 7,5k - 10k",
      min: 7500,
      max: 10000,
      key: "bin_75k_10k" as const,
    },
    {
      faixa: "R$ 10k - 12,5k",
      min: 10000,
      max: 12500,
      key: "bin_10k_125k" as const,
    },
    {
      faixa: "R$ 12,5k - 15k",
      min: 12500,
      max: 15000,
      key: "bin_125k_15k" as const,
    },
    {
      faixa: "R$ 15k - 17,5k",
      min: 15000,
      max: 17500,
      key: "bin_15k_175k" as const,
    },
    {
      faixa: "R$ 17,5k - 20k",
      min: 17500,
      max: 20000,
      key: "bin_175k_20k" as const,
    },
    {
      faixa: "> R$ 20k",
      min: 20000,
      max: Infinity,
      key: "bin_acima_20k" as const,
    },
  ];

  return BINS.map((bin) => ({
    faixa: bin.faixa,
    min: bin.min,
    max: bin.max,
    count: Number(row?.[bin.key] ?? 0),
  }));
}

/**
 * Retorna a folha por agrupamento departamental a partir de `fct_pessoal_departamento_metricas`.
 */
export async function getDepartmentalPayrollMetrics(
  portalSlug: string,
  year: number,
  empresaIds?: string[] | null,
): Promise<DepartmentalPayrollMetricsDTO[]> {
  if (!portalSlug || Number.isNaN(year)) return [];
  if (Array.isArray(empresaIds) && empresaIds.length === 0) return [];

  let query = db
    .selectFrom("fct_pessoal_departamento_metricas")
    .select((eb) => [
      "descricao",
      eb.fn.sum<string>("total_pago").as("total_pago"),
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "=", year);

  if (empresaIds && empresaIds.length > 0) {
    query = query.where("empresa_id", "in", empresaIds);
  }

  const rows = await query
    .groupBy("descricao")
    .orderBy("total_pago", "desc")
    .execute();

  return rows.map((r) => ({
    descricao: String(r.descricao || ""),
    pago: parseFloat(String(r.total_pago ?? "0")) || 0,
  }));
}
