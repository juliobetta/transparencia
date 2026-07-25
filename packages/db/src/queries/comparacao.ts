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
  mes_inicio: number;
  mes_fim: number;
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
    empenhado: calculateDelta(sumA.total_empenhado, sumB.total_empenhado),
    dotacao: calculateDelta(sumA.total_dotacao, sumB.total_dotacao),
  };

  // Pessoal
  const folhaA = await getFolhaVsServicos([specA.year]);
  const folhaB = await getFolhaVsServicos([specB.year]);
  const folhaRowA = folhaA[0] || { total_folha: 0, percentual_folha: 0 };
  const folhaRowB = folhaB[0] || { total_folha: 0, percentual_folha: 0 };

  const pessoalDelta = {
    total_folha: calculateDelta(folhaRowA.total_folha, folhaRowB.total_folha),
    percentual_folha: calculateDelta(
      folhaRowA.percentual_folha,
      folhaRowB.percentual_folha,
    ),
  };

  // Receitas
  const recA = await getFontesReceita([specA.year]);
  const recB = await getFontesReceita([specB.year]);
  const rRowA = recA[0] || {
    receita_propria: 0,
    transferencias_uniao: 0,
    transferencias_estado: 0,
    total: 0,
    pct_propria: 0,
  };
  const rRowB = recB[0] || {
    receita_propria: 0,
    transferencias_uniao: 0,
    transferencias_estado: 0,
    total: 0,
    pct_propria: 0,
  };

  const receitasDelta = {
    receita_propria: calculateDelta(
      rRowA.receita_propria,
      rRowB.receita_propria,
    ),
    transferencias_uniao: calculateDelta(
      rRowA.transferencias_uniao,
      rRowB.transferencias_uniao,
    ),
    transferencias_estado: calculateDelta(
      rRowA.transferencias_estado,
      rRowB.transferencias_estado,
    ),
    total: calculateDelta(rRowA.total, rRowB.total),
    pct_propria: calculateDelta(rRowA.pct_propria, rRowB.pct_propria),
  };

  // Licitações
  const gapsA = await getLicitacaoGaps(specA.year);
  const gapsB = await getLicitacaoGaps(specB.year);

  const licitacoesDelta = {
    sem_licitacao: calculateDelta(gapsA.length, gapsB.length),
    acima_limite: calculateDelta(
      gapsA.filter((g) => g.acima_limite).length,
      gapsB.filter((g) => g.acima_limite).length,
    ),
    saude: calculateDelta(
      gapsA.filter((g) => g.acima_limite && g.orgao_saude).length,
      gapsB.filter((g) => g.acima_limite && g.orgao_saude).length,
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
    valor_licitacao: calculateDelta(
      adesaoA.total_licitacao,
      adesaoB.total_licitacao,
    ),
    valor_contratos: calculateDelta(adesaoA.valor, adesaoB.valor),
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
