import { describe, expect, it } from "vitest";
import {
  getAdesaoDeAta,
  getAnaliseDespesasMetrics,
  getConcentracaoFornecedores,
  getDepartmentalPayroll,
  getDistribucaoModalidades,
  getDistribuicaoProventos,
  getEntidades,
  getExecucaoDecimoTerceiro,
  getExecucaoOrcamentaria,
  getExecucaoOrcamentariaMetrics,
  getFolhaVsServicos,
  getFontesReceita,
  getFontesReceitaMetrics,
  getHistoriaCapremMetrics,
  getHistoriaSaude,
  getHistoriaSaudeMetrics,
  getImpactoGastosLocais,
  getLicitacaoGaps,
  getPortalConfig,
  getPosicaoFiscal,
  getPosicaoFiscalMetrics,
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
  it("deve buscar posição fiscal via mart atômico com consolidação por empresas", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    if (empresaIds.length === 0) return; // banco de testes sem entidades, skip

    // Cenário 1: empresa única
    const metricsSingle = await getPosicaoFiscalMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      [empresaIds[0]],
    );
    expect(metricsSingle).not.toBeNull();
    if (metricsSingle !== null) {
      expect(typeof metricsSingle.portalSlug).toBe("string");
      expect(typeof metricsSingle.ano).toBe("number");
      expect(typeof metricsSingle.totalArrecadado).toBe("number");
      expect(typeof metricsSingle.despesasPagas).toBe("number");
      expect(typeof metricsSingle.restosPagosNoAno).toBe("number");
      expect(typeof metricsSingle.restosPendentesAdmAnterior).toBe("number");
      expect(typeof metricsSingle.restosPendentesAdmAtual).toBe("number");
      expect(typeof metricsSingle.saldoEstimado).toBe("number");
    }

    // Cenário 2: múltiplas empresas — consolidação (SUM)
    if (empresaIds.length > 1) {
      const metricsMulti = await getPosicaoFiscalMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
        empresaIds,
      );
      expect(metricsMulti).not.toBeNull();
      if (metricsMulti !== null && metricsSingle !== null) {
        // consolidado >= individual para campos sempre não-negativos
        expect(metricsMulti.totalArrecadado).toBeGreaterThanOrEqual(
          metricsSingle.totalArrecadado,
        );
      }
    }

    // Cenário 3: lista vazia retorna null imediatamente
    const metricsEmpty = await getPosicaoFiscalMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      [],
    );
    expect(metricsEmpty).toBeNull();
  });

  it("deve buscar analise de despesas via mart atômico (getAnaliseDespesasMetrics) com consolidação", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const metrics = await getAnaliseDespesasMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );
    expect(Array.isArray(metrics)).toBe(true);
    if (metrics.length > 0) {
      expect(typeof metrics[0].portalSlug).toBe("string");
      expect(typeof metrics[0].orgaoCodigo).toBe("string");
      expect(typeof metrics[0].unidadeCodigo).toBe("string");
      expect(typeof metrics[0].funcaoCodigo).toBe("string");
      expect(typeof metrics[0].ano).toBe("number");
      expect(typeof metrics[0].totalEmpenhado).toBe("number");
      expect(typeof metrics[0].totalLiquidado).toBe("number");
      expect(typeof metrics[0].totalPago).toBe("number");
    }

    const emptyFilter = await getAnaliseDespesasMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toEqual([]);
  });

  it("deve buscar execução orçamentária via mart atômico (getExecucaoOrcamentariaMetrics) com consolidação", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const metrics = await getExecucaoOrcamentariaMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );
    expect(Array.isArray(metrics)).toBe(true);
    if (metrics.length > 0) {
      expect(typeof metrics[0].portalSlug).toBe("string");
      expect(typeof metrics[0].orgaoCodigo).toBe("string");
      expect(typeof metrics[0].unidadeCodigo).toBe("string");
      expect(typeof metrics[0].funcaoCodigo).toBe("string");
      expect(typeof metrics[0].subfuncaoCodigo).toBe("string");
      expect(typeof metrics[0].ano).toBe("number");
      expect(typeof metrics[0].totalDotacaoAtualizada).toBe("number");
      expect(typeof metrics[0].totalEmpenhado).toBe("number");
      expect(typeof metrics[0].taxaExecucao).toBe("number");
      expect(typeof metrics[0].alertaExecucao).toBe("string");
    }

    const emptyFilter = await getExecucaoOrcamentariaMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toEqual([]);
  });

  it("deve buscar fontes de receita via mart atômico (getFontesReceitaMetrics) com consolidação", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const metrics = await getFontesReceitaMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );
    if (metrics !== null) {
      expect(typeof metrics.portalSlug).toBe("string");
      expect(typeof metrics.ano).toBe("number");
      expect(typeof metrics.receitaPropriaArrecadado).toBe("number");
      expect(typeof metrics.totalArrecadado).toBe("number");
      expect(typeof metrics.pctPropria).toBe("number");
      expect(typeof metrics.alertaDependencia).toBe("boolean");
      expect(typeof metrics.fpmArrecadado).toBe("number");
      expect(typeof metrics.emendasTotalArrecadado).toBe("number");
    }

    const emptyFilter = await getFontesReceitaMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toBeNull();
  });

  it("deve buscar história previdenciária via mart atômico (getHistoriaCapremMetrics) com restrição de portal", async () => {
    const metrics = await getHistoriaCapremMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
    );
    if (metrics !== null) {
      expect(typeof metrics.historiaCapremId).toBe("string");
      expect(typeof metrics.portalSlug).toBe("string");
      expect(typeof metrics.ano).toBe("number");
      expect(typeof metrics.totalAporteExigido).toBe("number");
      expect(typeof metrics.taxaAdimplenciaAporte).toBe("number");
      expect(typeof metrics.totalEmpenhadoPatronal).toBe("number");
      expect(typeof metrics.romboPatronalNaoRepassado).toBe("number");
    }

    const otherPortal = await getHistoriaCapremMetrics(
      "outra_cidade_prefeitura",
      TEST_YEAR,
    );
    expect(otherPortal).toBeNull();
  });

  it("deve buscar história da saúde via mart atômico (getHistoriaSaudeMetrics)", async () => {
    const metrics = await getHistoriaSaudeMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
    );
    if (metrics !== null) {
      expect(typeof metrics.historiaSaudeId).toBe("string");
      expect(typeof metrics.portalSlug).toBe("string");
      expect(typeof metrics.ano).toBe("number");
      expect(typeof metrics.dotacaoTotal).toBe("number");
      expect(typeof metrics.medicamentosInsumosPago).toBe("number");
      expect(typeof metrics.judicializacaoPago).toBe("number");
      expect(typeof metrics.hhiConcentracaoFornecedores).toBe("number");
    }
  });
});
