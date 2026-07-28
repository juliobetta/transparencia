import { describe, expect, it } from "vitest";
import {
  getAdesaoDeAta,
  getConcentracaoFornecedores,
  getDepartmentalPayroll,
  getDistribucaoModalidades,
  getDistribuicaoProventos,
  getEntidades,
  getExecucaoDecimoTerceiro,
  getExecucaoOrcamentaria,
  getFolhaVsServicos,
  getFontesReceita,
  getHistoriaSaude,
  getImpactoGastosLocais,
  getLicitacaoGaps,
  getPortalConfig,
  getPosicaoFiscal,
  getPrincipaisBeneficiariosDiarias,
  getResumoDiarias,
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
    expect(exec[0]).toHaveProperty("dotacaoAtualizada");
    expect(exec[0]).toHaveProperty("empenhado");
    expect(exec[0]).toHaveProperty("pago");
  });

  it("deve calcular fontes de receita com progresso", async () => {
    const fontes = await getFontesReceita([TEST_YEAR]);
    expect(Array.isArray(fontes)).toBe(true);
    if (fontes.length > 0) {
      expect(typeof fontes[0].totalPrevisto).toBe("number");
      expect(typeof fontes[0].totalArrecadado).toBe("number");
      expect(typeof fontes[0].emendasTotalArrecadado).toBe("number");
      expect(typeof fontes[0].emendasPixArrecadado).toBe("number");
      expect(typeof fontes[0].emendasIndividuaisArrecadado).toBe("number");
      expect(typeof fontes[0].fpmArrecadado).toBe("number");
      expect(typeof fontes[0].icmsArrecadado).toBe("number");
      expect(typeof fontes[0].issIptuArrecadado).toBe("number");
    }
  });

  it("deve buscar lacunas de licitação e distribuição de modalidades", async () => {
    const gaps = await getLicitacaoGaps(TEST_YEAR);
    expect(Array.isArray(gaps)).toBe(true);

    const dist = await getDistribucaoModalidades(TEST_YEAR);
    expect(Array.isArray(dist)).toBe(true);
  });

  it("deve calcular impacto de gastos locais e resumo de restos a pagar", async () => {
    const impacto = await getImpactoGastosLocais({
      year: TEST_YEAR,
      cidadeClean: "PORCIUNCULA",
      portalSlug: "porciuncula_prefeitura",
    });
    expect(impacto).toBeDefined();
    expect(typeof impacto.localPago).toBe("number");
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
      expect(typeof config.portalSlug).toBe("string");
      expect(typeof config.displayName).toBe("string");
      expect(typeof config.uf).toBe("string");
      expect(typeof config.anoInicial).toBe("number");
      expect(typeof config.empresaPadrao).toBe("string");
    }
  });

  it("deve buscar lista de entidades", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    expect(Array.isArray(entidades)).toBe(true);
  });

  it("deve calcular resumo de diárias e principais beneficiários", async () => {
    const resumo = await getResumoDiarias(TEST_YEAR);
    expect(resumo).toBeDefined();
    expect(typeof resumo.totalValor).toBe("number");
    expect(typeof resumo.totalViajantes).toBe("number");
    expect(typeof resumo.mediaReembolso).toBe("number");

    const beneficiarios = await getPrincipaisBeneficiariosDiarias({
      year: TEST_YEAR,
    });
    expect(Array.isArray(beneficiarios)).toBe(true);
  });

  it("deve buscar execução do 13º salário, distribuição de proventos e folha departamental", async () => {
    const decimoTerceiro = await getExecucaoDecimoTerceiro(TEST_YEAR);
    if (decimoTerceiro) {
      expect(typeof decimoTerceiro.empenhado).toBe("number");
      expect(typeof decimoTerceiro.pago).toBe("number");
      expect(typeof decimoTerceiro.pctPago).toBe("number");
    }

    const distProventos = await getDistribuicaoProventos(TEST_YEAR);
    expect(Array.isArray(distProventos)).toBe(true);
    expect(distProventos.length).toBe(9);

    const departmental = await getDepartmentalPayroll(TEST_YEAR);
    expect(Array.isArray(departmental)).toBe(true);
  });

  it("deve calcular folha vs servicos acumulado a partir de fct_despesas e LRF", async () => {
    const folha = await getFolhaVsServicos({ years: [TEST_YEAR] });
    expect(Array.isArray(folha)).toBe(true);
    if (folha.length > 0) {
      expect(typeof folha[0].totalFolha).toBe("number");
      expect(typeof folha[0].percentualFolha).toBe("number");
      expect(folha[0].percentualFolha).toBeGreaterThan(20);
      expect(folha[0].percentualFolha).toBeLessThan(54);
    }
  });
  it("deve calcular historia da saude corretamente", async () => {
    const saude = await getHistoriaSaude(TEST_YEAR);
    expect(saude).toBeDefined();
    expect(saude.orcamento).toBeDefined();
    expect(typeof saude.orcamento.liquidado).toBe("number");
    expect(typeof saude.orcamento.pago).toBe("number");
    expect(typeof saude.fontesReceita.repassesPrefeitura).toBe("number");
    expect(saude.licitacoesSaude).toBeDefined();
    expect(saude.emendasStats).toBeDefined();
  });
});
