import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import {
  getHistoriaSaudeMetrics,
  getSaudeFornecedoresCountMetrics,
} from "../historia-saude-metrics";

describe("getHistoriaSaudeMetrics", () => {
  it("deve buscar história da saúde via mart atômico", async () => {
    const metrics = await getHistoriaSaudeMetrics(PORTAL_SLUG, TEST_YEAR);
    if (metrics !== null) {
      expect(typeof metrics.historiaSaudeId).toBe("string");
      expect(typeof metrics.portalSlug).toBe("string");
      expect(typeof metrics.ano).toBe("number");
      expect(typeof metrics.dotacaoTotal).toBe("number");
      expect(typeof metrics.medicamentosInsumosEmpenhado).toBe("number");
      expect(typeof metrics.medicamentosInsumosPago).toBe("number");
      expect(typeof metrics.judicializacaoEmpenhado).toBe("number");
      expect(typeof metrics.judicializacaoPago).toBe("number");
      expect(typeof metrics.hhiConcentracaoFornecedores).toBe("number");
    }
  });
});

describe("getSaudeFornecedoresCountMetrics", () => {
  it("deve buscar fornecedores ativos da Saúde", async () => {
    const saudeFornecedoresCount = await getSaudeFornecedoresCountMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      ["2"],
    );
    expect(typeof saudeFornecedoresCount).toBe("number");
    expect(saudeFornecedoresCount).toBeGreaterThanOrEqual(0);
  });
});
