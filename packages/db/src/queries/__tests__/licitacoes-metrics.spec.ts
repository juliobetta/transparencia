import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import {
  getAdesaoDeAtaMetrics,
  getAdesaoExternaMetrics,
  getAnomaliasContratuaisMetrics,
  getDistribucaoModalidadesMetrics,
  getLicitacaoGapsMetrics,
} from "../licitacoes-metrics";

describe("licitacoes-metrics", () => {
  it("deve buscar métricas de Licitações via leitores atômicos *-metrics", async () => {
    const gaps = await getLicitacaoGapsMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(Array.isArray(gaps)).toBe(true);

    const modalidades = await getDistribucaoModalidadesMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
    );
    expect(Array.isArray(modalidades)).toBe(true);

    const adesao = await getAdesaoDeAtaMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(adesao).toBeDefined();
    expect(typeof adesao.quantidade).toBe("number");

    const adesaoExt = await getAdesaoExternaMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(adesaoExt).toBeDefined();

    const anomalias = await getAnomaliasContratuaisMetrics(
      PORTAL_SLUG,
      TEST_YEAR,
    );
    expect(anomalias).toBeDefined();
    expect(Array.isArray(anomalias.fracionamento)).toBe(true);
  });

  it("deve conter o limite_dispensa pré-calculado pelo dbt mart nos gaps sem licitação", async () => {
    const gaps = await getLicitacaoGapsMetrics(PORTAL_SLUG, TEST_YEAR);
    if (gaps.length > 0) {
      expect(typeof gaps[0].limiteDispensa).toBe("number");
      expect(gaps[0].limiteDispensa).toBeGreaterThan(0);
    }
  });
});
