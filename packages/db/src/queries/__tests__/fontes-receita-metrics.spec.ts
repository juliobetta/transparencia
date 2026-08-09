import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import { getFontesReceitaMetrics } from "../fontes-receita-metrics";
import { getEntidades } from "../metadata";

describe("getFontesReceitaMetrics", () => {
  it("deve buscar fontes de receita via mart atômico com consolidação", async () => {
    const entidades = await getEntidades(PORTAL_SLUG);
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const metrics = await getFontesReceitaMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );
    if (metrics !== null) {
      expect(typeof metrics.portalSlug).toBe("string");
      expect(typeof metrics.ano).toBe("number");
      expect(typeof metrics.receitaPropriaArrecadado).toBe("number");
      expect(typeof metrics.totalArrecadado).toBe("number");
      expect(typeof metrics.pctPropria).toBe("number");
      expect(typeof metrics.alertaDependencia).toBe("boolean");
      expect(typeof metrics.fpmArrecadado).toBe("number");
      expect(typeof metrics.receitaExtraOrcamentariaArrecadado).toBe("number");
    }

    const emptyFilter = await getFontesReceitaMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toBeNull();
  });
});
