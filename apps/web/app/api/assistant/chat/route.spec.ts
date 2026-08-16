import type { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";
import { POST } from "./route";

vi.mock("@/lib/agent/react-engine", () => ({
  executeReActAgent: vi.fn().mockResolvedValue({
    answer: "No exercício de 2025, o total foi de R$ 50.000.000,00.",
    metrics: [
      { title: "Arrecadado", value: "R$ 50.000.000,00" },
      { title: "Pago", value: "R$ 45.000.000,00" },
      { title: "Saldo", value: "R$ 5.000.000,00" },
    ],
    chartType: "bar",
    sqlQuery: "SELECT * FROM fct_posicao_fiscal_metricas",
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

  it("deve executar via ReAct agent e retornar resposta estruturada", async () => {
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
});
