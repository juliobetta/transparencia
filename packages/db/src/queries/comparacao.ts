import { getAdesaoDeAta } from "./adesao_de_ata";
import { getConcentracaoFornecedores } from "./concentracao_fornecedores";
import {
  getExecucaoOrcamentaria,
  summarizeExecucao,
} from "./execucao_orcamentaria";
import { getFolhaVsServicos } from "./folha_vs_servicos";
import { getFontesReceita } from "./fontes_receita";
import { getLicitacaoGaps } from "./licitacao_gaps";

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

export async function runComparacao(
  specA: PeriodSpec,
  specB: PeriodSpec,
): Promise<Record<string, Record<string, DeltaValue>>> {
  // Despesas
  const itemsA = await getExecucaoOrcamentaria(specA.year);
  const itemsB = await getExecucaoOrcamentaria(specB.year);
  const sumA = summarizeExecucao(itemsA);
  const sumB = summarizeExecucao(itemsB);

  const despesasDelta = {
    empenhado: calculateDelta(sumA.totalEmpenhado, sumB.totalEmpenhado),
    dotacao: calculateDelta(sumA.totalDotacao, sumB.totalDotacao),
  };

  // Pessoal
  const folhaA = await getFolhaVsServicos([specA.year]);
  const folhaB = await getFolhaVsServicos([specB.year]);
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
  const recA = await getFontesReceita([specA.year]);
  const recB = await getFontesReceita([specB.year]);
  const rRowA = recA[0] || {
    receitaPropria: 0,
    transferenciasUniao: 0,
    transferenciasEstado: 0,
    total: 0,
    pctPropria: 0,
  };
  const rRowB = recB[0] || {
    receitaPropria: 0,
    transferenciasUniao: 0,
    transferenciasEstado: 0,
    total: 0,
    pctPropria: 0,
  };

  const receitasDelta = {
    receitaPropria: calculateDelta(rRowA.receitaPropria, rRowB.receitaPropria),
    transferenciasUniao: calculateDelta(
      rRowA.transferenciasUniao,
      rRowB.transferenciasUniao,
    ),
    transferenciasEstado: calculateDelta(
      rRowA.transferenciasEstado,
      rRowB.transferenciasEstado,
    ),
    total: calculateDelta(rRowA.total, rRowB.total),
    pctPropria: calculateDelta(rRowA.pctPropria, rRowB.pctPropria),
  };

  // Licitações
  const gapsA = await getLicitacaoGaps(specA.year);
  const gapsB = await getLicitacaoGaps(specB.year);

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
  const fornA = await getConcentracaoFornecedores(specA.year);
  const fornB = await getConcentracaoFornecedores(specB.year);

  const fornecedoresDelta = {
    hhi: calculateDelta(fornA.hhi, fornB.hhi),
  };

  // Adesão
  const adesaoA = await getAdesaoDeAta(specA.year, ["2"]);
  const adesaoB = await getAdesaoDeAta(specB.year, ["2"]);

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
