import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import {
  getDepartmentalPayrollMetrics,
  getDistribuicaoProventosMetrics,
  getExecucaoDecimoTerceiroMetrics,
  getFolhaVsServicosMetrics,
  getPercentualChefiasEfetivasMetrics,
} from "../pessoal-metrics";

describe("pessoal-metrics", () => {
  it("deve buscar métricas de Pessoal via leitores atômicos *-metrics", async () => {
    const folha = await getFolhaVsServicosMetrics({
      years: [TEST_YEAR],
      portalSlug: PORTAL_SLUG,
    });
    expect(Array.isArray(folha)).toBe(true);

    const decimo13 = await getExecucaoDecimoTerceiroMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
    );
    if (decimo13) {
      expect(typeof decimo13.pago).toBe("number");
    }

    const chefias = await getPercentualChefiasEfetivasMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
    );
    if (chefias !== null) {
      expect(typeof chefias).toBe("number");
    }

    const proventos = await getDistribuicaoProventosMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
    );
    expect(Array.isArray(proventos)).toBe(true);
    expect(proventos.length).toBe(9);

    const dept = await getDepartmentalPayrollMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(Array.isArray(dept)).toBe(true);
  });
});
