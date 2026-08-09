import { describe, expect, it } from "vitest";
import type { loadOrcamentoData } from "./loader";
import { buildOrcamentoViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadOrcamentoData>>;

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    portalSlug: "porciuncula_prefeitura",
    context: {
      selectedYear: 2024,
      isCurrentYear: false,
      entidadesIds: undefined,
    },
    items: [],
    funcionalData: [],
    summary: {
      totalDotacao: 1000,
      totalEmpenhado: 800,
      totalLiquidado: 700,
      totalPago: 600,
      taxaExecucao: 80,
    },
    ...overrides,
  } as unknown as RawData;
}

describe("buildOrcamentoViewModel", () => {
  it("calcula os percentuais de execução relativos à dotação", () => {
    const vm = buildOrcamentoViewModel(makeRaw());
    expect(vm.empPct).toBe(80);
    expect(vm.liqPct).toBe(70);
    expect(vm.pagPct).toBe(60);
  });

  it("evita divisão por zero quando a dotação é zero", () => {
    const vm = buildOrcamentoViewModel(
      makeRaw({
        summary: {
          totalDotacao: 0,
          totalEmpenhado: 0,
          totalLiquidado: 0,
          totalPago: 0,
          taxaExecucao: 0,
        },
      }),
    );
    expect(vm.empPct).toBe(0);
    expect(vm.liqPct).toBe(0);
    expect(vm.pagPct).toBe(0);
  });

  it("agrupa funcionalData por função somando pago (ou empenhado como fallback)", () => {
    const vm = buildOrcamentoViewModel(
      makeRaw({
        funcionalData: [
          { funcaoNome: "Saúde", empenhado: 100, pago: 90 },
          { funcaoNome: "Saúde", empenhado: 50, pago: 40 },
          { funcaoNome: "Educação", empenhado: 200, pago: 0 },
        ],
      }),
    );

    const saude = vm.funcItems.find((f) => f.funcao === "Saúde");
    const educacao = vm.funcItems.find((f) => f.funcao === "Educação");
    expect(saude?.valor).toBe(130);
    // pago=0 cai no fallback para empenhado
    expect(educacao?.valor).toBe(200);
  });

  it("ordena funcItems por valor decrescente", () => {
    const vm = buildOrcamentoViewModel(
      makeRaw({
        funcionalData: [
          { funcaoNome: "Pequena", empenhado: 10, pago: 10 },
          { funcaoNome: "Grande", empenhado: 500, pago: 500 },
        ],
      }),
    );
    expect(vm.funcItems[0].funcao).toBe("Grande");
  });
});
