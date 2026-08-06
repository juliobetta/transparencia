import { getConcentracaoFornecedoresMetrics } from "./despesas-metrics";
import { getExecucaoOrcamentariaMetrics } from "./execucao-orcamentaria-metrics";
import { getFontesReceitaMetrics } from "./fontes-receita-metrics";
import {
  getAdesaoDeAtaMetrics,
  getLicitacaoGapsMetrics,
} from "./licitacoes-metrics";
import { getFolhaVsServicosMetrics } from "./pessoal-metrics";

export interface PeriodSpec {
  year: number;
  mesInicio: number;
  mesFim: number;
}

export interface DeltaValue {
  a: number;
  b: number;
  abs: number;
  pct: number | null;
}

function calculateDelta(a: number, b: number): DeltaValue {
  return {
    a,
    b,
    abs: b - a,
    pct: a !== 0 ? ((b - a) / a) * 100 : null,
  };
}

// biome-ignore lint/complexity/useMaxParams: signature requires specA, specB, portalSlug, empresaIds for compatibility
export async function runComparacao(
  specA: PeriodSpec,
  specB: PeriodSpec,
  portalSlug: string = "porciuncula_prefeitura",
  empresaIds: string[] = [],
): Promise<Record<string, Record<string, DeltaValue>>> {
  // Despesas
  const itemsA = await getExecucaoOrcamentariaMetrics(
    portalSlug,
    specA.year,
    empresaIds,
  );
  const itemsB = await getExecucaoOrcamentariaMetrics(
    portalSlug,
    specB.year,
    empresaIds,
  );
  const sumA = {
    totalEmpenhado: itemsA.reduce((acc, i) => acc + i.totalEmpenhado, 0),
    totalDotacao: itemsA.reduce((acc, i) => acc + i.totalDotacaoAtualizada, 0),
  };
  const sumB = {
    totalEmpenhado: itemsB.reduce((acc, i) => acc + i.totalEmpenhado, 0),
    totalDotacao: itemsB.reduce((acc, i) => acc + i.totalDotacaoAtualizada, 0),
  };

  const despesasDelta = {
    empenhado: calculateDelta(sumA.totalEmpenhado, sumB.totalEmpenhado),
    dotacao: calculateDelta(sumA.totalDotacao, sumB.totalDotacao),
  };

  // Pessoal
  const folhaA = await getFolhaVsServicosMetrics({
    years: [specA.year],
    portalSlug,
    empresaIds,
  });
  const folhaB = await getFolhaVsServicosMetrics({
    years: [specB.year],
    portalSlug,
    empresaIds,
  });
  const folhaRowA = folhaA[0] || { totalFolha: 0, percentualFolha: 0 };
  const folhaRowB = folhaB[0] || { totalFolha: 0, percentualFolha: 0 };

  const pessoalDelta = {
    totalFolha: calculateDelta(folhaRowA.totalFolha, folhaRowB.totalFolha),
    percentualFolha: calculateDelta(
      folhaRowA.percentualFolha,
      folhaRowB.percentualFolha,
    ),
  };

  // Receitas
  const recA = await getFontesReceitaMetrics(
    portalSlug,
    specA.year,
    empresaIds,
  );
  const recB = await getFontesReceitaMetrics(
    portalSlug,
    specB.year,
    empresaIds,
  );
  const rRowA = recA || {
    receitaPropriaArrecadado: 0,
    transferenciasUniaoArrecadado: 0,
    transferenciasEstadoArrecadado: 0,
    totalArrecadado: 0,
    pctPropria: 0,
  };
  const rRowB = recB || {
    receitaPropriaArrecadado: 0,
    transferenciasUniaoArrecadado: 0,
    transferenciasEstadoArrecadado: 0,
    totalArrecadado: 0,
    pctPropria: 0,
  };

  const receitasDelta = {
    receitaPropria: calculateDelta(
      rRowA.receitaPropriaArrecadado,
      rRowB.receitaPropriaArrecadado,
    ),
    transferenciasUniao: calculateDelta(
      rRowA.transferenciasUniaoArrecadado,
      rRowB.transferenciasUniaoArrecadado,
    ),
    transferenciasEstado: calculateDelta(
      rRowA.transferenciasEstadoArrecadado,
      rRowB.transferenciasEstadoArrecadado,
    ),
    total: calculateDelta(rRowA.totalArrecadado, rRowB.totalArrecadado),
    pctPropria: calculateDelta(rRowA.pctPropria, rRowB.pctPropria),
  };

  // Licitações
  const gapsA = await getLicitacaoGapsMetrics(
    portalSlug,
    specA.year,
    empresaIds,
  );
  const gapsB = await getLicitacaoGapsMetrics(
    portalSlug,
    specB.year,
    empresaIds,
  );

  const licitacoesDelta = {
    semLicitacao: calculateDelta(gapsA.length, gapsB.length),
    acimaLimite: calculateDelta(
      gapsA.filter((g) => g.acimaLimite).length,
      gapsB.filter((g) => g.acimaLimite).length,
    ),
    saude: calculateDelta(
      gapsA.filter((g) => g.acimaLimite && g.orgaoSaude).length,
      gapsB.filter((g) => g.acimaLimite && g.orgaoSaude).length,
    ),
  };

  // Fornecedores
  const fornA = await getConcentracaoFornecedoresMetrics(
    portalSlug,
    specA.year,
    empresaIds,
  );
  const fornB = await getConcentracaoFornecedoresMetrics(
    portalSlug,
    specB.year,
    empresaIds,
  );

  const fornecedoresDelta = {
    hhi: calculateDelta(fornA.hhi, fornB.hhi),
  };

  // Adesão
  const adesaoA = await getAdesaoDeAtaMetrics(
    portalSlug,
    specA.year,
    empresaIds,
  );
  const adesaoB = await getAdesaoDeAtaMetrics(
    portalSlug,
    specB.year,
    empresaIds,
  );

  const adesaoDelta = {
    quantidade: calculateDelta(adesaoA.quantidade, adesaoB.quantidade),
    valorLicitacao: calculateDelta(
      adesaoA.totalLicitacao,
      adesaoB.totalLicitacao,
    ),
    valorContratos: calculateDelta(adesaoA.valor, adesaoB.valor),
  };

  return {
    despesas: despesasDelta,
    pessoal: pessoalDelta,
    receitas: receitasDelta,
    licitacoes: licitacoesDelta,
    fornecedores: fornecedoresDelta,
    adesao: adesaoDelta,
  };
}
