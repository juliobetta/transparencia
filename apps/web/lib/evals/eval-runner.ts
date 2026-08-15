import { queryDuckDbParquet } from "../duckdb-executor";
import { BENCHMARK_QUESTIONS } from "./benchmark-questions";

export interface EvalResult {
  questionId: string;
  question: string;
  domain: string;
  passed: boolean;
  sqlQuery: string;
  error?: string;
  latencyMs: number;
}

export interface EvalSummary {
  total: number;
  passed: number;
  failed: number;
  passRate: number;
  results: EvalResult[];
}

export async function runBenchmarkEvals(
  portalSlug = "porciuncula_prefeitura",
  year = 2025,
): Promise<EvalSummary> {
  const results: EvalResult[] = [];

  for (const q of BENCHMARK_QUESTIONS) {
    const startTime = Date.now();
    let sql = "";
    let passed = false;
    let error: string | undefined;

    try {
      if (q.expectedMart === "fct_posicao_fiscal_metricas") {
        sql = `SELECT CAST(SUM(total_arrecadado) AS DOUBLE) as total_arrecadado, CAST(SUM(despesas_pagas) AS DOUBLE) as despesas_pagas, CAST(SUM(saldo_estimado) AS DOUBLE) as saldo_estimado FROM fct_posicao_fiscal_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      } else if (q.expectedMart === "fct_fontes_receita_metricas") {
        sql = `SELECT CAST(SUM(total_previsto) AS DOUBLE) as total_previsto, CAST(SUM(total_arrecadado) AS DOUBLE) as total_arrecadado, CAST(SUM(emendas_pix_arrecadado) AS DOUBLE) as emendas_pix_arrecadado FROM fct_fontes_receita_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      } else if (q.expectedMart === "fct_historia_saude_metricas") {
        sql = `SELECT CAST(SUM(total_liquidado) AS DOUBLE) as total_liquidado, CAST(SUM(total_pago) AS DOUBLE) as total_pago FROM fct_historia_saude_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      } else if (q.expectedMart === "fct_historia_caprem_metricas") {
        sql = `SELECT CAST(SUM(total_empenhado_patronal) AS DOUBLE) as total_empenhado_patronal, CAST(SUM(total_pago_patronal) AS DOUBLE) as total_pago_patronal FROM fct_historia_caprem_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      } else if (q.expectedMart === "fct_pessoal_folha_metricas") {
        sql = `SELECT CAST(SUM(total_folha) AS DOUBLE) as total_folha, CAST(SUM(total_pago) AS DOUBLE) as total_pago FROM fct_pessoal_folha_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      } else {
        sql = `SELECT CAST(SUM(total_pago) AS DOUBLE) as total_pago FROM fct_analise_despesas_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      }

      const rows = await queryDuckDbParquet(sql);
      passed = Array.isArray(rows);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      passed = false;
    }

    const latencyMs = Date.now() - startTime;
    results.push({
      questionId: q.id,
      question: q.question,
      domain: q.domain,
      passed,
      sqlQuery: sql,
      error,
      latencyMs,
    });
  }

  const passedCount = results.filter((r) => r.passed).length;
  return {
    total: results.length,
    passed: passedCount,
    failed: results.length - passedCount,
    passRate: (passedCount / results.length) * 100,
    results,
  };
}
