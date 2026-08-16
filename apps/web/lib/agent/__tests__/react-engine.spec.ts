import { describe, expect, it, vi } from "vitest";
import { executeReActAgent } from "../react-engine";

vi.mock("ai", () => ({
  generateText: vi.fn().mockResolvedValue({
    text: "Pensamento: vou consultar os marts. Ação: executou query.",
    steps: [{ stepType: "tool-call" }, { stepType: "tool-result" }],
  }),
  generateObject: vi.fn().mockResolvedValue({
    object: {
      answer: "Resposta do agente ReAct para o cidadão",
      metrics: [{ title: "Arrecadado", value: "R$ 50.000.000,00" }],
      chartType: "bar",
    },
  }),
  jsonSchema: vi.fn((s) => s),
  tool: vi.fn((config) => config),
}));

vi.mock("@ai-sdk/google", () => ({
  google: vi.fn(),
  createGoogleGenerativeAI: vi.fn(() => vi.fn()),
}));

vi.mock("../../duckdb-executor", () => ({
  queryDuckDbParquet: vi
    .fn()
    .mockResolvedValue([
      { total_arrecadado: 50000000, despesas_pagas: 45000000 },
    ]),
}));

describe("ReAct Engine com Auto-Correção", () => {
  it("deve executar o ciclo ReAct e retornar resposta estruturada para o cidadão", async () => {
    process.env.GEMINI_API_KEY = "test-key";

    const result = await executeReActAgent({
      message: "Qual o total arrecadado no ano?",
      portalSlug: "porciuncula_prefeitura",
      year: 2025,
    });

    expect(result.answer).toContain("Resposta do agente ReAct");
    expect(result.metrics).toHaveLength(1);
    expect(result.stepsCount).toBe(2);
    expect(result.autoCorrected).toBe(false);
  });
});
