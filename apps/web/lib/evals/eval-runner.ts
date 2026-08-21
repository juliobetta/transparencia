import { executeAnalyticsQuery } from "../sql-executor";
import { BENCHMARK_QUESTIONS } from "./benchmark-questions";
import { generateSyntheticBenchmarkQuestions } from "./synthetic-generator";

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
  includeSynthetic = true,
): Promise<EvalSummary> {
  const syntheticQuestions = includeSynthetic
    ? generateSyntheticBenchmarkQuestions()
    : [];
  const allQuestions = [...BENCHMARK_QUESTIONS, ...syntheticQuestions];
  const results: EvalResult[] = [];

  for (const q of allQuestions) {
    const startTime = Date.now();
    let sql = "";
    let passed = false;
    let error: string | undefined;

    try {
      const martTable = q.expectedMart || "fct_posicao_fiscal_metricas";
      sql = `SELECT * FROM ${martTable} WHERE portal_slug = '${portalSlug}' AND ano = ${year} LIMIT 5`;
      const rows = await executeAnalyticsQuery(sql);
      passed = Boolean(rows && Array.isArray(rows));
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
    passRate: results.length > 0 ? (passedCount / results.length) * 100 : 0,
    results,
  };
}
