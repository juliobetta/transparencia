import { describe, expect, it } from "vitest";
import {
  getAdesaoDeAta,
  getConcentracaoFornecedores,
  getEntidades,
  getExecucaoOrcamentaria,
  getFontesReceita,
  getImpactoGastosLocais,
  getLicitacaoGaps,
  getPortalConfig,
  getPosicaoFiscal,
  getTendenciasAnuais,
} from "../index";

describe("queries Kysely (paridade e integridade contábil)", () => {
  const TEST_YEAR = 2025;

  it("deve calcular posição fiscal sem erros", async () => {
    const posicao = await getPosicaoFiscal(TEST_YEAR);
    expect(posicao).toBeDefined();
    expect(typeof posicao.totalArrecadado).toBe("number");
    expect(typeof posicao.despesasPagas).toBe("number");
    expect(typeof posicao.totalSaidas).toBe("number");
    expect(typeof posicao.saldoEstimado).toBe("number");
  });

  it("deve calcular execução orçamentária por unidade", async () => {
    const exec = await getExecucaoOrcamentaria(TEST_YEAR);
    expect(Array.isArray(exec)).toBe(true);
    expect(exec.length).toBeGreaterThan(0);
    expect(exec[0]).toHaveProperty("dotacao_atualizada");
    expect(exec[0]).toHaveProperty("empenhado");
    expect(exec[0]).toHaveProperty("pago");
  });

  it("deve calcular fontes de receita com progresso", async () => {
    const fontes = await getFontesReceita([TEST_YEAR]);
    expect(Array.isArray(fontes)).toBe(true);
    if (fontes.length > 0) {
      expect(typeof fontes[0].total_previsto).toBe("number");
      expect(typeof fontes[0].total_arrecadado).toBe("number");
    }
  });

  it("deve buscar lacunas de licitação", async () => {
    const gaps = await getLicitacaoGaps(TEST_YEAR);
    expect(Array.isArray(gaps)).toBe(true);
  });

  it("deve calcular impacto de gastos locais e resumo de restos a pagar", async () => {
    const impacto = await getImpactoGastosLocais({
      year: TEST_YEAR,
      cidadeClean: "PORCIUNCULA",
      portalSlug: "porciuncula_prefeitura",
    });
    expect(impacto).toBeDefined();
    expect(typeof impacto.local_pago).toBe("number");
  });

  it("deve buscar adessões de ata", async () => {
    const adesao = await getAdesaoDeAta(TEST_YEAR);
    expect(adesao).toBeDefined();
    expect(typeof adesao.quantidade).toBe("number");
  });

  it("deve calcular concentração de fornecedores e HHI", async () => {
    const conc = await getConcentracaoFornecedores(TEST_YEAR);
    expect(conc).toBeDefined();
    expect(Array.isArray(conc.top10)).toBe(true);
    expect(typeof conc.hhi).toBe("number");
  });

  it("deve buscar tendências anuais", async () => {
    const tend = await getTendenciasAnuais([2024, 2025]);
    expect(Array.isArray(tend)).toBe(true);
  });

  it("deve buscar portal config", async () => {
    const config = await getPortalConfig("porciuncula_prefeitura");
    if (config) {
      expect(typeof config.portal_slug).toBe("string");
      expect(typeof config.display_name).toBe("string");
      expect(typeof config.uf).toBe("string");
      expect(typeof config.ano_inicial).toBe("number");
      expect(typeof config.empresa_padrao).toBe("string");
    }
  });

  it("deve buscar lista de entidades", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    expect(Array.isArray(entidades)).toBe(true);
  });
});
