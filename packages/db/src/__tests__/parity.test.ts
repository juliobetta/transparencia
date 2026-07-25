import { describe, expect, it } from "vitest";
import { getAdesaoDeAta } from "../queries/adesao_de_ata";
import { getConcentracaoFornecedores } from "../queries/concentracao_fornecedores";
import {
  getExecucaoOrcamentaria,
  summarizeExecucao,
} from "../queries/execucao_orcamentaria";
import { getFontesReceita } from "../queries/fontes_receita";
import { getLicitacaoGaps } from "../queries/licitacao_gaps";
import { getPosicaoFiscal } from "../queries/posicao_fiscal";
import { getTendenciasAnuais } from "../queries/tendencias_anuais";

describe("Testes de Paridade Kysely DB (@transparencia/db)", () => {
  const TEST_YEAR = 2025;

  it("deve buscar fontes de receita sem erros", async () => {
    const res = await getFontesReceita([TEST_YEAR]);
    expect(res).toBeDefined();
    expect(Array.isArray(res)).toBe(true);
    if (res.length > 0) {
      expect(res[0].ano).toBe(TEST_YEAR);
      expect(typeof res[0].total_arrecadado).toBe("number");
    }
  });

  it("deve buscar posição fiscal sem erros", async () => {
    const res = await getPosicaoFiscal(TEST_YEAR);
    expect(res).toBeDefined();
    expect(typeof res.total_arrecadado).toBe("number");
    expect(typeof res.total_saidas).toBe("number");
    expect(Array.isArray(res.restos_pendentes)).toBe(true);
  });

  it("deve buscar execução orçamentária e resumir corretamente", async () => {
    const items = await getExecucaoOrcamentaria(TEST_YEAR);
    expect(Array.isArray(items)).toBe(true);
    const summary = summarizeExecucao(items);
    expect(typeof summary.total_empenhado).toBe("number");
    expect(typeof summary.total_pago).toBe("number");
  });

  it("deve buscar licitação gaps sem erros", async () => {
    const gaps = await getLicitacaoGaps(TEST_YEAR);
    expect(Array.isArray(gaps)).toBe(true);
  });

  it("deve buscar adesão de ata sem erros", async () => {
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
});
