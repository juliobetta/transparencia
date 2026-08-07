import { describe, expect, it } from "vitest";
import {
  getAdesaoDeAtaMetrics,
  getAdesaoExternaMetrics,
  getAnaliseDespesasMetrics,
  getAnomaliasContratuaisMetrics,
  getCapremActuarialTrendMetrics,
  getCapremCadprevMetrics,
  getCapremEntidadesMetrics,
  getCapremNaturezaMetrics,
  getConcentracaoFornecedoresMetrics,
  getDepartmentalPayrollMetrics,
  getDespesasPorUnidadeMetrics,
  getDistribucaoModalidadesMetrics,
  getDistribuicaoProventosMetrics,
  getEntidades,
  getExecucaoDecimoTerceiroMetrics,
  getExecucaoOrcamentariaMetrics,
  getFolhaVsServicosMetrics,
  getFontesReceitaMetrics,
  getHistoriaCapremMetrics,
  getHistoriaSaudeMetrics,
  getImpactoGastosLocaisMetrics,
  getLicitacaoGapsMetrics,
  getOrcamentoFuncionalMetrics,
  getPercentualChefiasEfetivasMetrics,
  getPortalConfig,
  getPosicaoFiscalDetalhesMetrics,
  getPosicaoFiscalMetrics,
  getPrincipaisBeneficiariosDiariasMetrics,
  getRestosAPagarResumoMetrics,
  getResumoDiariasMetrics,
  getSaudeFornecedoresCountMetrics,
} from "../index";

describe("queries Kysely (paridade e integridade contábil via leitores de métricas)", () => {
  const TEST_YEAR = 2025;

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

  it("deve buscar detalhes de posição fiscal via mart atômico (getPosicaoFiscalDetalhesMetrics)", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const details = await getPosicaoFiscalDetalhesMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );

    expect(details).toBeDefined();
    expect(details.restosPendentesTotal).toBeGreaterThanOrEqual(0);
    expect(details.restosPendentesAnteriores).toBeGreaterThanOrEqual(0);
    expect(Array.isArray(details.restosPendentes)).toBe(true);
    expect(Array.isArray(details.topCredoresAdmAtual)).toBe(true);
    expect(typeof details.totalCredoresAdmAtual).toBe("number");

    const emptyFilter = await getPosicaoFiscalDetalhesMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      [],
    );
    expect(emptyFilter).toEqual({
      portalSlug: "porciuncula_prefeitura",
      ano: TEST_YEAR,
      restosPendentesTotal: 0,
      restosPendentesAnteriores: 0,
      restosPendentes: [],
      topCredoresAdmAtual: [],
      totalCredoresAdmAtual: 0,
    });
  });

  it("deve buscar orçamento funcional via mart atômico (getOrcamentoFuncionalMetrics)", async () => {
    const entidades = await getEntidades("porciuncula_prefeitura");
    const empresaIds = entidades.map((e: { id: string }) => e.id);

    const funcional = await getOrcamentoFuncionalMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      empresaIds.length > 0 ? empresaIds : ["1"],
    );

    expect(Array.isArray(funcional)).toBe(true);
    if (funcional.length > 0) {
      expect(typeof funcional[0].funcaoNome).toBe("string");
      expect(typeof funcional[0].subfuncaoNome).toBe("string");
      expect(typeof funcional[0].dotacaoAtualizada).toBe("number");
      expect(typeof funcional[0].empenhado).toBe("number");
      expect(typeof funcional[0].liquidado).toBe("number");
      expect(typeof funcional[0].pago).toBe("number");
    }

    const emptyFilter = await getOrcamentoFuncionalMetrics(
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
      expect(typeof metrics.medicamentosInsumosEmpenhado).toBe("number");
      expect(typeof metrics.medicamentosInsumosPago).toBe("number");
      expect(typeof metrics.judicializacaoEmpenhado).toBe("number");
      expect(typeof metrics.judicializacaoPago).toBe("number");
      expect(typeof metrics.hhiConcentracaoFornecedores).toBe("number");
    }
  });

  it("deve buscar métricas de despesas diárias, fornecedores, restos e unidades via leitores atômicos", async () => {
    const resumoDiarias = await getResumoDiariasMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      ["1"],
    );
    expect(resumoDiarias).toBeDefined();
    expect(typeof resumoDiarias.totalValor).toBe("number");

    const beneficiarios = await getPrincipaisBeneficiariosDiariasMetrics({
      portalSlug: "porciuncula_prefeitura",
      year: TEST_YEAR,
      limit: 5,
      empresaIds: ["1"],
    });
    expect(Array.isArray(beneficiarios)).toBe(true);

    const impacto = await getImpactoGastosLocaisMetrics({
      portalSlug: "porciuncula_prefeitura",
      year: TEST_YEAR,
      empresaIds: ["1"],
      cidadeClean: "PORCIUNCULA",
    });
    expect(impacto).toBeDefined();

    const conc = await getConcentracaoFornecedoresMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      ["1"],
    );
    expect(conc).toBeDefined();

    const restos = await getRestosAPagarResumoMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      ["1"],
    );
    expect(restos).toBeDefined();
    expect(typeof restos.dividaMaisAntigaAno).toBe("number");
    expect(restos.dividaMaisAntigaAno).toBeGreaterThanOrEqual(2000);

    const unidades = await getDespesasPorUnidadeMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      ["1"],
    );
    expect(Array.isArray(unidades)).toBe(true);

    const capremEntidades = await getCapremEntidadesMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
    );
    expect(Array.isArray(capremEntidades)).toBe(true);

    const saudeFornecedoresCount = await getSaudeFornecedoresCountMetrics(
      "porciuncula_prefeitura",
      TEST_YEAR,
      ["2"],
    );
    expect(typeof saudeFornecedoresCount).toBe("number");
    expect(saudeFornecedoresCount).toBeGreaterThanOrEqual(0);
  });

  describe("Regressão e Integridade Fiscais (Despesas, Saúde, CAPREM)", () => {
    it("deve garantir integridade contábil de restos a pagar e dívida mais antiga", async () => {
      const restos = await getRestosAPagarResumoMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
        ["1", "2", "3", "02.01", "02.04"],
      );
      expect(restos).toBeDefined();
      expect(restos.totalPendente).toBeGreaterThan(0);
      expect(restos.fornecedoresAguardando).toBeGreaterThan(0);
      expect(restos.dividaMaisAntigaAno).toBeLessThanOrEqual(2022);
      expect(restos.topFornecedores.length).toBeGreaterThan(0);
    });

    it("deve calcular o impacto de compras locais e concentração HHI sem inflação de folha", async () => {
      const impacto = await getImpactoGastosLocaisMetrics({
        portalSlug: "porciuncula_prefeitura",
        year: TEST_YEAR,
        empresaIds: ["1", "2", "3", "02.01", "02.04"],
        cidadeClean: "PORCIUNCULA",
      });
      expect(impacto).toBeDefined();
      expect(impacto.pctLocal).toBeGreaterThan(10);
      expect(impacto.pctLocal).toBeLessThan(50);

      const conc = await getConcentracaoFornecedoresMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
        ["1", "2", "3", "02.01", "02.04"],
      );
      expect(conc).toBeDefined();
      expect(conc.hhi).toBeGreaterThan(500);
      expect(conc.hhi).toBeLessThan(1200);
    });

    it("deve calcular fornecedores ativos da Saúde sem omitir credores", async () => {
      const count = await getSaudeFornecedoresCountMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
        ["2", "02.04"],
      );
      expect(count).toBeGreaterThan(100);
    });

    it("deve calcular amortização de dívidas e déficit patronal do CAPREM sem distorção", async () => {
      const caprem = await getHistoriaCapremMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(caprem).not.toBeNull();
      if (caprem) {
        expect(caprem.totalAmortizacaoDivida).toBeGreaterThan(100000);
        expect(caprem.totalEmpenhadoPatronal).toBeGreaterThan(
          caprem.totalPagoPatronal,
        );
        expect(caprem.romboPatronalNaoRepassado).toBeGreaterThan(500000);
      }

      const entidadesCaprem = await getCapremEntidadesMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(entidadesCaprem)).toBe(true);
      expect(entidadesCaprem.length).toBeGreaterThan(0);

      const capremNatureza = await getCapremNaturezaMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(capremNatureza)).toBe(true);

      const capremTrend = await getCapremActuarialTrendMetrics(
        "porciuncula_prefeitura",
      );
      expect(Array.isArray(capremTrend)).toBe(true);

      const capremCadprev = await getCapremCadprevMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(capremCadprev)).toBe(true);
    });

    it("deve buscar métricas de Pessoal e Licitações via leitores atômicos *-metrics", async () => {
      const folha = await getFolhaVsServicosMetrics({
        years: [TEST_YEAR],
        portalSlug: "porciuncula_prefeitura",
      });
      expect(Array.isArray(folha)).toBe(true);

      const decimo13 = await getExecucaoDecimoTerceiroMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      if (decimo13) {
        expect(typeof decimo13.pago).toBe("number");
      }

      const chefias = await getPercentualChefiasEfetivasMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      if (chefias !== null) {
        expect(typeof chefias).toBe("number");
      }

      const proventos = await getDistribuicaoProventosMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(proventos)).toBe(true);
      expect(proventos.length).toBe(9);

      const dept = await getDepartmentalPayrollMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(dept)).toBe(true);

      const gaps = await getLicitacaoGapsMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(gaps)).toBe(true);

      const modalidades = await getDistribucaoModalidadesMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(Array.isArray(modalidades)).toBe(true);

      const adesao = await getAdesaoDeAtaMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(adesao).toBeDefined();
      expect(typeof adesao.quantidade).toBe("number");

      const adesaoExt = await getAdesaoExternaMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(adesaoExt).toBeDefined();

      const anomalias = await getAnomaliasContratuaisMetrics(
        "porciuncula_prefeitura",
        TEST_YEAR,
      );
      expect(anomalias).toBeDefined();
      expect(Array.isArray(anomalias.fracionamento)).toBe(true);
    });
  });
});
