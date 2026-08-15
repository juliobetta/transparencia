import { describe, expect, it, vi } from "vitest";
import { POST } from "./route";

// Mock do Vercel AI SDK
vi.mock("ai", () => ({
  generateObject: vi.fn().mockResolvedValue({
    object: {
      sql: "SELECT total_arrecadado FROM fct_posicao_fiscal_metricas",
      answer: "Resposta do modelo em linguagem simples",
      metrics: [{ title: "Arrecadado", value: "R$ 50.000.000,00" }],
      chartType: "bar",
    },
  }),
  jsonSchema: vi.fn((schema) => schema),
}));

vi.mock("@ai-sdk/google", () => ({
  google: vi.fn(),
}));

// Mock do executor DuckDB Parquet
vi.mock("@/lib/duckdb-executor", () => ({
  queryDuckDbParquet: vi.fn().mockImplementation(async (sql: string) => {
    if (sql.includes("fct_posicao_fiscal_metricas")) {
      return [
        {
          total_arrecadado: 50000000,
          despesas_pagas: 45000000,
          saldo_estimado: 5000000,
        },
      ];
    }
    if (sql.includes("fct_fontes_receita_metricas")) {
      return [
        {
          receita_total_prevista: 60000000,
          receita_total_arrecadada: 50000000,
          emendas_pix_arrecadado: 1200000,
        },
      ];
    }
    return [];
  }),
}));

describe("POST /api/assistant/chat", () => {
  it("deve retornar erro 400 se a mensagem estiver vazia", async () => {
    const req = new Request("http://localhost/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify({ message: "" }),
    });

    const res = await POST(req as unknown as NextRequest);
    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json.error).toBeDefined();
  });

  it("deve retornar métricas de Posição Fiscal", async () => {
    const req = new Request("http://localhost/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify({
        message: "Qual a posição fiscal e total arrecadado?",
        portalSlug: "porciuncula_prefeitura",
        ano: "2025",
      }),
    });

    const res = await POST(req as unknown as NextRequest);
    expect(res.status).toBe(200);
    const json = await res.json();

    expect(json.answer).toContain("exercício de");
    expect(json.metrics).toHaveLength(3);
    expect(json.chartType).toBe("bar");
    expect(json.sqlQuery).toContain("fct_posicao_fiscal_metricas");
  });

  it("deve retornar métricas de Receita e Emendas PIX", async () => {
    const req = new Request("http://localhost/api/assistant/chat", {
      method: "POST",
      body: JSON.stringify({
        message: "Quanto foi recebido em emendas pix?",
        portalSlug: "porciuncula_prefeitura",
        ano: "2025",
      }),
    });

    const res = await POST(req as unknown as NextRequest);
    expect(res.status).toBe(200);
    const json = await res.json();

    expect(json.answer).toBeDefined();
    expect(json.metrics).toBeDefined();
  });
});
