import { FISCAL_TAXONOMY } from "../mcp/transparencia-mcp";
import type { BenchmarkQuestion } from "./benchmark-questions";

const QUESTION_TEMPLATES = [
  {
    pattern: (desc: string) => `Qual o total consolidado de ${desc}?`,
    metrics: ["total_pago", "total_arrecadado", "total_empenhado"],
  },
  {
    pattern: (desc: string) =>
      `Como foram os valores empenhados e pagamentos de ${desc} no exercício?`,
    metrics: ["total_empenhado", "total_pago"],
  },
  {
    pattern: (desc: string) =>
      `Existem pendências ou alertas cadastrados sobre ${desc}?`,
    metrics: ["saldo_estimado", "status_execucao"],
  },
];

export function generateSyntheticBenchmarkQuestions(): BenchmarkQuestion[] {
  const generated: BenchmarkQuestion[] = [];
  let index = 1;

  for (const mart of FISCAL_TAXONOMY) {
    for (const tmpl of QUESTION_TEMPLATES) {
      const id = `syn-${String(index++).padStart(3, "0")}`;
      generated.push({
        id,
        domain: mart.domain,
        question: tmpl.pattern(mart.description.toLowerCase()),
        expectedMart: mart.tableName,
        expectedMetrics: mart.columns.filter((c) =>
          tmpl.metrics.some((m) => c.includes(m)),
        ),
      });
    }
  }

  return generated;
}
