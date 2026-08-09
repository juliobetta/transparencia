import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import { getEntidades } from "../metadata";
import { getPosicaoFiscalDetalhesMetrics } from "../posicao-fiscal-detalhes-metrics";

describe("getPosicaoFiscalDetalhesMetrics", () => {
  it("deve buscar detalhes de posição fiscal via mart atômico", async () => {
    const entidades = await getEntidades(PORTAL_SLUG);
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const details = await getPosicaoFiscalDetalhesMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );

    expect(details).toBeDefined();
    expect(details.restosPendentesTotal).toBeGreaterThanOrEqual(0);
    expect(details.restosPendentesAnteriores).toBeGreaterThanOrEqual(0);
    expect(Array.isArray(details.restosPendentes)).toBe(true);
    expect(Array.isArray(details.topCredoresAdmAtual)).toBe(true);
    expect(typeof details.totalCredoresAdmAtual).toBe("number");

    const emptyFilter = await getPosicaoFiscalDetalhesMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toEqual({
      portalSlug: PORTAL_SLUG,
      ano: TEST_YEAR,
      restosPendentesTotal: 0,
      restosPendentesAnteriores: 0,
      restosPendentes: [],
      topCredoresAdmAtual: [],
      totalCredoresAdmAtual: 0,
    });
  });
});
