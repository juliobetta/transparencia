import { describe, expect, it, vi } from "vitest";
import { runBenchmarkEvals } from "../eval-runner";

vi.mock("../duckdb-executor", () => ({
  queryDuckDbParquet: vi.fn().mockResolvedValue([{ total_arrecadado: 1000 }]),
}));

describe("AI Evals Benchmark Runner", () => {
  it("deve executar a suíte de perguntas de benchmark e calcular a taxa de sucesso", async () => {
    const summary = await runBenchmarkEvals("porciuncula_prefeitura", 2025);
    expect(summary.total).toBe(10);
    expect(summary.passed).toBe(10);
    expect(summary.failed).toBe(0);
    expect(summary.passRate).toBe(100);
    expect(summary.results[0].passed).toBe(true);
  });
});
