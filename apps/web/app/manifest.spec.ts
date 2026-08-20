import { describe, expect, it } from "vitest";
import manifest from "./manifest";

describe("PWA Manifest", () => {
  it("returns correct MetadataRoute.Manifest metadata with screenshots and any/maskable icons", () => {
    const config = manifest();

    expect(config.name).toBe("MaisTransparencia");
    expect(config.short_name).toBe("MaisTransparencia");
    expect(config.display).toBe("standalone");
    expect(config.start_url).toBe("/?mode=standalone");
    expect(config.background_color).toBe("#0f172a");
    expect(config.theme_color).toBe("#1e3a8a");

    expect(config.icons).toEqual([
      {
        src: "/favicon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/favicon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/favicon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/favicon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ]);

    expect(config.screenshots).toEqual([
      {
        src: "/screenshot-desktop.png",
        sizes: "1280x720",
        type: "image/png",
        form_factor: "wide",
        label: "Portal de Transparência Municipal no Desktop",
      },
      {
        src: "/screenshot-mobile.png",
        sizes: "390x844",
        type: "image/png",
        form_factor: "narrow",
        label: "Portal de Transparência Municipal no Mobile",
      },
    ]);
  });
});
