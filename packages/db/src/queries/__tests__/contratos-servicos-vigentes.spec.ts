import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import { getContratosServicosVigentes } from "../contratos-servicos-vigentes";

describe("getContratosServicosVigentes", () => {
  it("deve buscar contratos de serviços vigentes via leitor atômico", async () => {
    const list = await getContratosServicosVigentes(PORTAL_SLUG, TEST_YEAR);
    expect(Array.isArray(list)).toBe(true);

    if (list.length > 0) {
      const item = list[0];
      expect(typeof item.portalSlug).toBe("string");
      expect(typeof item.fornecedorNome).toBe("string");
      expect(typeof item.fornecedorCnpj).toBe("string");
      expect(typeof item.objetoDescricao).toBe("string");
      expect(typeof item.totalEmpenhado).toBe("number");
      expect(typeof item.totalLiquidado).toBe("number");
      expect(typeof item.totalPago).toBe("number");
      expect(typeof item.saldoPendente).toBe("number");
      expect(typeof item.percentualPago).toBe("number");
      expect(["em_execucao", "concluido", "inexecutado"]).toContain(
        item.statusExecucao,
      );
      expect(item.totalEmpenhado).toBeGreaterThanOrEqual(item.totalLiquidado);
      expect(item.totalLiquidado).toBeGreaterThanOrEqual(item.totalPago);
    }
  });
});
