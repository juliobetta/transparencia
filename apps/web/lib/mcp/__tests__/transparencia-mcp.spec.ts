import { describe, expect, it, vi } from "vitest";
import {
  createTransparenciaMcpServer,
  FISCAL_TAXONOMY,
  trackMcpToolCall,
} from "../transparencia-mcp";

vi.mock("../../posthog-server", () => ({
  getPostHogServer: () => ({
    capture: vi.fn(),
    flush: vi.fn().mockResolvedValue(undefined),
  }),
}));

describe("Transparencia MCP Server", () => {
  it("deve conter a taxonomia dos domínios fiscais canônicos", () => {
    expect(FISCAL_TAXONOMY.length).toBeGreaterThan(0);
    const posicaoFiscal = FISCAL_TAXONOMY.find(
      (d) => d.domain === "Posição Fiscal",
    );
    expect(posicaoFiscal).toBeDefined();
    expect(posicaoFiscal?.marts[0].table).toBe("fct_posicao_fiscal_metricas");
  });

  it("deve instanciar o servidor MCP corretamente", () => {
    const server = createTransparenciaMcpServer();
    expect(server).toBeDefined();
  });

  it("deve rastrear chamadas de ferramentas via trackMcpToolCall", async () => {
    await expect(
      trackMcpToolCall("query_duckdb_mart", {
        input: { sql: "SELECT 1" },
        output: { row_count: 1 },
        latencyMs: 120,
      }),
    ).resolves.not.toThrow();
  });
});
