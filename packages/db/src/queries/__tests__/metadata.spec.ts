import { describe, expect, it } from "vitest";
import { PORTAL_SLUG } from "../../test-helpers";
import { getEntidades, getPortalConfig } from "../metadata";

describe("metadata", () => {
  it("deve buscar portal config", async () => {
    const config = await getPortalConfig(PORTAL_SLUG);
    if (config) {
      expect(typeof config.portalSlug).toBe("string");
      expect(typeof config.displayName).toBe("string");
      expect(typeof config.uf).toBe("string");
      expect(typeof config.anoInicial).toBe("number");
      expect(typeof config.empresaPadrao).toBe("string");
    }
  });

  it("deve buscar lista de entidades", async () => {
    const entidades = await getEntidades(PORTAL_SLUG);
    expect(Array.isArray(entidades)).toBe(true);
  });
});
