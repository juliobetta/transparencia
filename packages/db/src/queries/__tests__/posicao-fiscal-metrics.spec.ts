import { afterEach, describe, expect, it } from "vitest";
import {
  cleanupFixtures,
  createFixturePortalSlug,
  seedPosicaoFiscal,
} from "../../../tests/fixtures/seed";
import { getPosicaoFiscalMetrics } from "../posicao-fiscal-metrics";

const PORTAL = createFixturePortalSlug();

afterEach(async () => {
  await cleanupFixtures(PORTAL);
});

describe("getPosicaoFiscalMetrics", () => {
  it("retorna os valores exatos semeados para uma única empresa", async () => {
    await seedPosicaoFiscal({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      totalArrecadado: 1000,
      despesasPagas: 400,
      restosPagosNoAno: 50,
      restosPendentesAdmAnterior: 20,
      restosPendentesAdmAtual: 10,
      saldoEstimado: 600,
    });

    const result = await getPosicaoFiscalMetrics(PORTAL, 2030, ["1"]);

    expect(result).toEqual({
      portalSlug: PORTAL,
      ano: 2030,
      totalArrecadado: 1000,
      despesasPagas: 400,
      restosPagosNoAno: 50,
      restosPendentesAdmAnterior: 20,
      restosPendentesAdmAtual: 10,
      saldoEstimado: 600,
    });
  });

  it("consolida (SUM) os campos numéricos quando múltiplas empresas são selecionadas", async () => {
    await seedPosicaoFiscal({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      totalArrecadado: 1000,
      despesasPagas: 400,
      saldoEstimado: 600,
    });
    await seedPosicaoFiscal({
      portalSlug: PORTAL,
      empresaId: "2",
      ano: 2030,
      totalArrecadado: 500,
      despesasPagas: 100,
      saldoEstimado: 380,
    });

    const result = await getPosicaoFiscalMetrics(PORTAL, 2030, ["1", "2"]);

    expect(result?.totalArrecadado).toBe(1500);
    expect(result?.despesasPagas).toBe(500);
    expect(result?.saldoEstimado).toBe(980);
  });

  it("ignora empresas fora do filtro empresaIds", async () => {
    await seedPosicaoFiscal({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      totalArrecadado: 1000,
    });
    await seedPosicaoFiscal({
      portalSlug: PORTAL,
      empresaId: "2",
      ano: 2030,
      totalArrecadado: 999_999,
    });

    const result = await getPosicaoFiscalMetrics(PORTAL, 2030, ["1"]);

    expect(result?.totalArrecadado).toBe(1000);
  });

  it("retorna null quando não há dados para o portal/ano informados", async () => {
    await seedPosicaoFiscal({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      totalArrecadado: 1000,
    });

    const result = await getPosicaoFiscalMetrics(PORTAL, 1999, ["1"]);

    expect(result).toBeNull();
  });

  it("retorna null imediatamente quando empresaIds está vazio, sem consultar o banco", async () => {
    const result = await getPosicaoFiscalMetrics(PORTAL, 2030, []);
    expect(result).toBeNull();
  });
});
