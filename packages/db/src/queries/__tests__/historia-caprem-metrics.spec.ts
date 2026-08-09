import { afterEach, describe, expect, it } from "vitest";
import {
  cleanupFixtures,
  createFixturePortalSlug,
  seedHistoriaCaprem,
} from "../../../tests/fixtures/seed";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import {
  getCapremActuarialTrendMetrics,
  getCapremCadprevMetrics,
  getCapremEntidadesMetrics,
  getCapremNaturezaMetrics,
  getHistoriaCapremMetrics,
} from "../historia-caprem-metrics";

const PORTAL = createFixturePortalSlug();

afterEach(async () => {
  await cleanupFixtures(PORTAL);
});

describe("getHistoriaCapremMetrics", () => {
  it("retorna os valores exatos semeados para o portal/ano", async () => {
    await seedHistoriaCaprem({
      portalSlug: PORTAL,
      ano: 2030,
      totalAporteExigido: 1000,
      totalAporteQuitado: 700,
      taxaAdimplenciaAporte: 70,
      totalEmpenhadoPatronal: 900,
      totalPagoPatronal: 500,
      romboPatronalNaoRepassado: 400,
      totalAmortizacaoDivida: 150,
      servidoresEfetivos: 30,
      servidoresTemporarios: 5,
    });

    const result = await getHistoriaCapremMetrics(PORTAL, 2030);

    expect(result).not.toBeNull();
    expect(result?.totalAporteExigido).toBe(1000);
    expect(result?.taxaAdimplenciaAporte).toBe(70);
    expect(result?.romboPatronalNaoRepassado).toBe(400);
    expect(result?.servidoresEfetivos).toBe(30);
  });

  it("respeita o isolamento por portal: retorna null para outro portal mesmo com dados no ano", async () => {
    await seedHistoriaCaprem({
      portalSlug: PORTAL,
      ano: 2030,
      totalAporteExigido: 1000,
    });

    const result = await getHistoriaCapremMetrics(
      "outro_portal_sem_dados",
      2030,
    );

    expect(result).toBeNull();
  });

  it("retorna null quando não há dados para o ano informado", async () => {
    await seedHistoriaCaprem({
      portalSlug: PORTAL,
      ano: 2030,
      totalAporteExigido: 1000,
    });

    const result = await getHistoriaCapremMetrics(PORTAL, 1999);

    expect(result).toBeNull();
  });
});

// As funções abaixo têm fallbacks e joins mais complexos (ver historia-caprem-metrics.ts);
// aqui só validamos que a camada de query não quebra e devolve o shape esperado mesmo
// contra tabelas vazias — a lógica de negócio em si já é coberta pelos testes dbt.
describe("getCapremEntidadesMetrics / getCapremNaturezaMetrics / getCapremActuarialTrendMetrics / getCapremCadprevMetrics (smoke)", () => {
  it("não quebram e retornam arrays mesmo sem dados", async () => {
    const entidades = await getCapremEntidadesMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(Array.isArray(entidades)).toBe(true);

    const natureza = await getCapremNaturezaMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(Array.isArray(natureza)).toBe(true);

    const trend = await getCapremActuarialTrendMetrics(PORTAL_SLUG);
    expect(Array.isArray(trend)).toBe(true);

    const cadprev = await getCapremCadprevMetrics(PORTAL_SLUG, TEST_YEAR);
    expect(Array.isArray(cadprev)).toBe(true);
  });
});
