import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import {
  deriveStatusExecucao,
  getContratosServicosVigentes,
} from "../contratos-servicos-vigentes";

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

  describe("deriveStatusExecucao", () => {
    it("deve classificar como inexecutado contrato vencido com liquidação zerada", () => {
      const status = deriveStatusExecucao({
        vencimentoAtual: "2024-12-31",
        totalEmpenhado: 10000,
        totalLiquidado: 0,
        totalPago: 0,
        ano: 2024,
        referenceDateISO: "2026-08-01",
      });
      expect(status).toBe("inexecutado");
    });

    it("deve classificar como inexecutado contrato de ano anterior com liquidação e pagamento zerados", () => {
      const status = deriveStatusExecucao({
        vencimentoAtual: null,
        totalEmpenhado: 15000,
        totalLiquidado: 0,
        totalPago: 0,
        ano: 2023,
        referenceDateISO: "2026-08-01",
      });
      expect(status).toBe("inexecutado");
    });

    it("deve classificar como concluido contrato totalmente pago (100%)", () => {
      const status = deriveStatusExecucao({
        vencimentoAtual: "2025-06-30",
        totalEmpenhado: 20000,
        totalLiquidado: 20000,
        totalPago: 20000,
        ano: 2025,
        referenceDateISO: "2026-08-01",
      });
      expect(status).toBe("concluido");
    });

    it("deve classificar como em_execucao contrato ativo dentro da vigência com execução parcial", () => {
      const status = deriveStatusExecucao({
        vencimentoAtual: "2027-12-31",
        totalEmpenhado: 50000,
        totalLiquidado: 25000,
        totalPago: 20000,
        ano: 2026,
        referenceDateISO: "2026-08-01",
      });
      expect(status).toBe("em_execucao");
    });
  });
});
