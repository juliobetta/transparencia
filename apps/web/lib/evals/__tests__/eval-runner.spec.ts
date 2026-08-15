import { describe, expect, it, vi } from "vitest";
import { runBenchmarkEvals } from "../eval-runner";

vi.mock("../duckdb-executor", () => ({
  queryDuckDbParquet: vi.fn().mockResolvedValue([{ total_arrecadado: 1000 }]),
}));

describe("AI Evals Benchmark Runner", () => {
  it("deve executar a suíte ampliada de perguntas manuais e sintéticas", async () => {
    const summary = await runBenchmarkEvals(
      "porciuncula_prefeitura",
      2025,
      true,
    );
    expect(summary.total).toBeGreaterThan(50);
    expect(summary.passed).toBe(summary.total);
    expect(summary.failed).toBe(0);
    expect(summary.passRate).toBe(100);
    expect(summary.results[0].passed).toBe(true);
  });
});
