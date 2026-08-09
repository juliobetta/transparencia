import { afterEach, describe, expect, it } from "vitest";
import {
  cleanupFixtures,
  createFixturePortalSlug,
  seedOrcamentoFuncional,
} from "../../../tests/fixtures/seed";
import { getOrcamentoFuncionalMetrics } from "../orcamento-funcional-metrics";

const PORTAL = createFixturePortalSlug();

afterEach(async () => {
  await cleanupFixtures(PORTAL);
});

describe("getOrcamentoFuncionalMetrics", () => {
  it("retorna uma linha por função/subfunção com os valores exatos semeados", async () => {
    await seedOrcamentoFuncional({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      funcaoNome: "Saúde",
      subfuncaoNome: "Atenção Básica",
      dotacaoAtualizada: 10_000,
      empenhado: 8_000,
      liquidado: 7_000,
      pago: 6_000,
    });

    const result = await getOrcamentoFuncionalMetrics(PORTAL, 2030, ["1"]);

    expect(result).toEqual([
      {
        funcaoNome: "Saúde",
        subfuncaoNome: "Atenção Básica",
        dotacaoAtualizada: 10_000,
        empenhado: 8_000,
        liquidado: 7_000,
        pago: 6_000,
      },
    ]);
  });

  it("retorna uma linha por função/subfunção distinta, sem consolidar", async () => {
    await seedOrcamentoFuncional({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      funcaoNome: "Saúde",
      subfuncaoNome: "Atenção Básica",
      empenhado: 100,
    });
    await seedOrcamentoFuncional({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      funcaoNome: "Educação",
      subfuncaoNome: "Ensino Fundamental",
      empenhado: 200,
    });

    const result = await getOrcamentoFuncionalMetrics(PORTAL, 2030, ["1"]);

    expect(result).toHaveLength(2);
    expect(result.map((r) => r.funcaoNome).sort()).toEqual([
      "Educação",
      "Saúde",
    ]);
  });

  it("ignora empresas fora do filtro empresaIds", async () => {
    await seedOrcamentoFuncional({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      funcaoNome: "Saúde",
      subfuncaoNome: "Atenção Básica",
    });
    await seedOrcamentoFuncional({
      portalSlug: PORTAL,
      empresaId: "2",
      ano: 2030,
      funcaoNome: "Educação",
      subfuncaoNome: "Ensino Fundamental",
    });

    const result = await getOrcamentoFuncionalMetrics(PORTAL, 2030, ["1"]);

    expect(result).toHaveLength(1);
    expect(result[0].funcaoNome).toBe("Saúde");
  });

  it("retorna [] quando empresaIds está vazio, sem consultar o banco", async () => {
    const result = await getOrcamentoFuncionalMetrics(PORTAL, 2030, []);
    expect(result).toEqual([]);
  });

  it("retorna [] quando não há dados para o portal/ano informados", async () => {
    await seedOrcamentoFuncional({
      portalSlug: PORTAL,
      empresaId: "1",
      ano: 2030,
      funcaoNome: "Saúde",
      subfuncaoNome: "Atenção Básica",
    });

    const result = await getOrcamentoFuncionalMetrics(PORTAL, 1999, ["1"]);
    expect(result).toEqual([]);
  });
});
