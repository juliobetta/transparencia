import {
  getHistoriaSaudeMetrics,
  getSaudeContratosCountMetrics,
  getSaudeEmendasMetrics,
  getSaudeExecutionTrendMetrics,
  getSaudeFontesReceitaMetrics,
  getSaudeFornecedoresCountMetrics,
  getSaudeLicitacoesMetrics,
  SAUDE_EMPRESA,
} from "@transparencia/db";

export interface SaudeSearchParams {
  ano?: string;
  entidades?: string;
}

export interface SaudeContext {
  selectedYear: number;
  isCurrentYear: boolean;
}

export function parseSaudeContext(
  searchParams: SaudeSearchParams,
): SaudeContext {
  const currentYear = new Date().getFullYear();
  const parsed = searchParams.ano ? Number(searchParams.ano) : currentYear;
  const selectedYear =
    Number.isInteger(parsed) && parsed > 1900 ? parsed : currentYear;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
  };
}

function requirePortalSlug(portalSlug: string): string {
  const normalized = portalSlug.trim();
  if (!normalized) {
    throw new Error("portalSlug vazio: o tenant deve ser informado.");
  }
  return normalized;
}

function classifyHhi(hhi: number): string {
  if (hhi >= 2500) return "alta";
  if (hhi >= 1500) return "moderada a alta";
  return "baixa";
}

export async function loadSaudeData(
  portalSlug: string,
  searchParams: SaudeSearchParams,
) {
  const tenantSlug = requirePortalSlug(portalSlug);
  const context = parseSaudeContext(searchParams);
  const empresaIds = searchParams.entidades
    ? searchParams.entidades.split(",").filter(Boolean)
    : [SAUDE_EMPRESA];

  const [
    saudeMetrics,
    executionTrend,
    emendasStats,
    contratosCount,
    fornecedoresCount,
    licitacoesSaude,
  ] = await Promise.all([
    getHistoriaSaudeMetrics(tenantSlug, context.selectedYear),
    getSaudeExecutionTrendMetrics(tenantSlug),
    getSaudeEmendasMetrics(tenantSlug, context.selectedYear, empresaIds),
    getSaudeContratosCountMetrics(tenantSlug, context.selectedYear, empresaIds),
    getSaudeFornecedoresCountMetrics(
      tenantSlug,
      context.selectedYear,
      empresaIds,
    ),
    getSaudeLicitacoesMetrics(tenantSlug, context.selectedYear, empresaIds),
  ]);

  const dotacao = saudeMetrics?.dotacaoTotal ?? 0;
  const empenhado = saudeMetrics?.totalEmpenhado ?? 0;
  const liquidado = saudeMetrics?.totalLiquidado ?? 0;
  const pago = saudeMetrics?.totalPago ?? 0;
  const medicamentosInsumosEmpenhado =
    saudeMetrics?.medicamentosInsumosEmpenhado ?? 0;
  const medicamentosInsumosPago = saudeMetrics?.medicamentosInsumosPago ?? 0;
  const judicializacaoEmpenhado = saudeMetrics?.judicializacaoEmpenhado ?? 0;
  const judicializacaoPago = saudeMetrics?.judicializacaoPago ?? 0;
  const emendasArrecadado = saudeMetrics?.emendasSaudeArrecadado ?? 0;
  const hhiVal = Math.round(saudeMetrics?.hhiConcentracaoFornecedores ?? 0);

  const fontesReceitaMetrics = await getSaudeFontesReceitaMetrics({
    portalSlug: tenantSlug,
    ano: context.selectedYear,
    empresaIds,
    empenhadoTotal: empenhado,
  });

  const saude = {
    orcamento: {
      dotacao,
      empenhado,
      liquidado,
      pago,
      taxaExecucao: dotacao > 0 ? empenhado / dotacao : 0,
      alertaSubExecucao:
        !context.isCurrentYear && dotacao > 0 && empenhado / dotacao < 0.7,
      medicamentosInsumos: medicamentosInsumosEmpenhado,
      medicamentosInsumosPago: medicamentosInsumosPago,
      judicializacao: judicializacaoEmpenhado,
      judicializacaoPago: judicializacaoPago,
      contratosVinculadosCount: contratosCount,
      fornecedoresAtivosCount: fornecedoresCount,
    },
    farmaceutica: {
      medicamentosInsumos: medicamentosInsumosEmpenhado,
      medicamentosInsumosPago: medicamentosInsumosPago,
      judicializacao: judicializacaoEmpenhado,
      judicializacaoPago: judicializacaoPago,
      hhi: hhiVal,
      hhiClassificacao: classifyHhi(hhiVal),
    },
    fontesReceita: {
      ...fontesReceitaMetrics,
      emendasParlamentares: emendasStats.totalAutorizado || emendasArrecadado,
    },
    executionTrend,
    licitacoesSaude,
    emendasStats,
    emendas: emendasStats.lista,
    emendasTotal: emendasStats.totalAutorizado || emendasArrecadado,
  };

  return {
    portalSlug: tenantSlug,
    context,
    saude,
  };
}
