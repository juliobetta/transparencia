import { describe, expect, it } from "vitest";
import { PORTAL_SLUG, TEST_YEAR } from "../../test-helpers";
import { getEntidades } from "../metadata";
import { getReceitasExtraOrcamentariasList } from "../receitas-extra-metrics";

describe("getReceitasExtraOrcamentariasList", () => {
  it("deve buscar receitas extra-orçamentárias via leitor atômico", async () => {
    const entidades = await getEntidades(PORTAL_SLUG);
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const list = await getReceitasExtraOrcamentariasList(
      PORTAL_SLUG,
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );
    expect(Array.isArray(list)).toBe(true);
    if (list.length > 0) {
      expect(typeof list[0].receitaExtraId).toBe("string");
      expect(typeof list[0].portalSlug).toBe("string");
      expect(typeof list[0].ano).toBe("number");
      expect(typeof list[0].valorArrecadado).toBe("number");
    }

    const emptyFilter = await getReceitasExtraOrcamentariasList(
      PORTAL_SLUG,
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toEqual([]);
  });
});
