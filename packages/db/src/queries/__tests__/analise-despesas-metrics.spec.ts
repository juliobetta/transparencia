import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import { getAnaliseDespesasMetrics } from "../analise-despesas-metrics";
import { getEntidades } from "../metadata";

describe("getAnaliseDespesasMetrics", () => {
  it("deve buscar analise de despesas via mart atômico com consolidação", async () => {
    const entidades = await getEntidades(PORTAL_SLUG);
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const metrics = await getAnaliseDespesasMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );
    expect(Array.isArray(metrics)).toBe(true);
    if (metrics.length > 0) {
      expect(typeof metrics[0].portalSlug).toBe("string");
      expect(typeof metrics[0].orgaoCodigo).toBe("string");
      expect(typeof metrics[0].unidadeCodigo).toBe("string");
      expect(typeof metrics[0].funcaoCodigo).toBe("string");
      expect(typeof metrics[0].ano).toBe("number");
      expect(typeof metrics[0].totalEmpenhado).toBe("number");
      expect(typeof metrics[0].totalLiquidado).toBe("number");
      expect(typeof metrics[0].totalPago).toBe("number");
    }

    const emptyFilter = await getAnaliseDespesasMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toEqual([]);
  });
});
