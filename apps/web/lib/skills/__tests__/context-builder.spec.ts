import { describe, expect, it } from "vitest";
import { buildLayeredContext, loadSkillMarkdown } from "../context-builder";

describe("Layered Context Builder", () => {
  it("deve carregar um arquivo de Skill em Markdown existente", () => {
    const markdown = loadSkillMarkdown("posicao-fiscal");
    expect(markdown).toContain("Posição Fiscal");
    expect(markdown).toContain("saldo_estimado");
  });

  it("deve construir o contexto em camadas completo com portal_slug e ano", () => {
    const context = buildLayeredContext({
      portalSlug: "porciuncula",
      year: 2025,
      currentRoute: "/posicao-fiscal",
    });

    expect(context).toContain('Portal Slug Ativo: "porciuncula"');
    expect(context).toContain("Exercício Fiscal Selecionado: 2025");
    expect(context).toContain("TAXONOMIA DOS MARTS FISCAIS DISPONÍVEIS");
    expect(context).toContain("fct_posicao_fiscal_metricas");
    expect(context).toContain(
      "FILTRAGEM POR ÁREA/ENTIDADE MUNICIPAL (EMPRESA_ID E DIM_ORGAO)",
    );
    expect(context).toContain("dim_orgao");
  });
});
