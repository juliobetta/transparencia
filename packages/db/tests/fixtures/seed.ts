import { randomUUID } from "node:crypto";
import { db } from "../../src/client";

/**
 * Cada arquivo de spec deve criar seu próprio slug via `createFixturePortalSlug()`
 * e usá-lo em todos os seeds/queries/cleanup daquele arquivo. O vitest roda
 * arquivos de teste em paralelo (workers/processos distintos) contra o mesmo
 * Postgres; um slug fixo compartilhado faria o cleanup de um arquivo apagar
 * dados que outro arquivo ainda está usando.
 */
export function createFixturePortalSlug(): string {
  return `fixture_test_${randomUUID()}`;
}

let seq = 0;
function nextId(prefix: string): string {
  seq += 1;
  return `${prefix}_${seq}`;
}

export interface PosicaoFiscalRow {
  portalSlug: string;
  empresaId: string;
  ano: number;
  totalArrecadado?: number;
  despesasPagas?: number;
  restosPagosNoAno?: number;
  restosPendentesAdmAnterior?: number;
  restosPendentesAdmAtual?: number;
  saldoEstimado?: number;
}

export async function seedPosicaoFiscal(row: PosicaoFiscalRow): Promise<void> {
  await db
    .insertInto("fct_posicao_fiscal_metricas")
    .values({
      posicao_fiscal_id: nextId("pf"),
      portal_slug: row.portalSlug,
      empresa_id: row.empresaId,
      ano: row.ano,
      total_arrecadado: row.totalArrecadado ?? 0,
      despesas_pagas: row.despesasPagas ?? 0,
      restos_pagos_no_ano: row.restosPagosNoAno ?? 0,
      restos_pendentes_adm_anterior: row.restosPendentesAdmAnterior ?? 0,
      restos_pendentes_adm_atual: row.restosPendentesAdmAtual ?? 0,
      saldo_estimado: row.saldoEstimado ?? 0,
    })
    .execute();
}

export interface OrcamentoFuncionalRow {
  portalSlug: string;
  empresaId: string;
  ano: number;
  funcaoNome: string;
  subfuncaoNome: string;
  dotacaoAtualizada?: number;
  empenhado?: number;
  liquidado?: number;
  pago?: number;
}

export async function seedOrcamentoFuncional(
  row: OrcamentoFuncionalRow,
): Promise<void> {
  await db
    .insertInto("fct_orcamento_funcional_metricas")
    .values({
      orcamento_funcional_id: nextId("of"),
      portal_slug: row.portalSlug,
      empresa_id: row.empresaId,
      ano: row.ano,
      funcao_nome: row.funcaoNome,
      subfuncao_nome: row.subfuncaoNome,
      dotacao_atualizada: row.dotacaoAtualizada ?? 0,
      empenhado: row.empenhado ?? 0,
      liquidado: row.liquidado ?? 0,
      pago: row.pago ?? 0,
    })
    .execute();
}

export interface HistoriaCapremRow {
  portalSlug: string;
  ano: number;
  totalAporteExigido?: number;
  totalAporteQuitado?: number;
  taxaAdimplenciaAporte?: number;
  totalEmpenhadoPatronal?: number;
  totalLiquidadoPatronal?: number;
  totalPagoPatronal?: number;
  romboPatronalNaoRepassado?: number;
  totalAmortizacaoDivida?: number;
  totalCaspPlanoSaude?: number;
  totalEmpenhado?: number;
  totalLiquidado?: number;
  totalPago?: number;
  servidoresEfetivos?: number;
  servidoresTemporarios?: number;
}

export async function seedHistoriaCaprem(
  row: HistoriaCapremRow,
): Promise<void> {
  await db
    .insertInto("fct_historia_caprem_metricas")
    .values({
      historia_caprem_id: nextId("hc"),
      portal_slug: row.portalSlug,
      ano: row.ano,
      total_aporte_exigido: row.totalAporteExigido ?? 0,
      total_aporte_quitado: row.totalAporteQuitado ?? 0,
      taxa_adimplencia_aporte: row.taxaAdimplenciaAporte ?? 0,
      total_empenhado_patronal: row.totalEmpenhadoPatronal ?? 0,
      total_liquidado_patronal: row.totalLiquidadoPatronal ?? 0,
      total_pago_patronal: row.totalPagoPatronal ?? 0,
      rombo_patronal_nao_repassado: row.romboPatronalNaoRepassado ?? 0,
      total_amortizacao_divida: row.totalAmortizacaoDivida ?? 0,
      total_casp_plano_saude: row.totalCaspPlanoSaude ?? 0,
      total_empenhado: row.totalEmpenhado ?? 0,
      total_liquidado: row.totalLiquidado ?? 0,
      total_pago: row.totalPago ?? 0,
      servidores_efetivos: row.servidoresEfetivos ?? 0,
      servidores_temporarios: row.servidoresTemporarios ?? 0,
    })
    .execute();
}

/** Remove tudo que os `seed*` acima inseriram para o `portalSlug` dado. */
export async function cleanupFixtures(portalSlug: string): Promise<void> {
  await db
    .deleteFrom("fct_posicao_fiscal_metricas")
    .where("portal_slug", "=", portalSlug)
    .execute();
  await db
    .deleteFrom("fct_orcamento_funcional_metricas")
    .where("portal_slug", "=", portalSlug)
    .execute();
  await db
    .deleteFrom("fct_historia_caprem_metricas")
    .where("portal_slug", "=", portalSlug)
    .execute();
}
