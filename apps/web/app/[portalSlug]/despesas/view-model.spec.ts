import { describe, expect, it } from "vitest";
import type { loadDespesasData } from "./loader";
import { buildDespesasViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadDespesasData>>;

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    context: {
      selectedYear: 2024,
      isCurrentYear: false,
      entidadesIds: undefined,
    },
    metricasGerais: {
      empenhado: 1000,
      liquidado: 800,
      pago: 700,
      taxaLiquidacao: 80,
      taxaPagamento: 70,
    },
    impactoLocais: {
      localPago: 600,
      externoPago: 100,
      pctLocal: 85.7,
      historicoPctLocal: 80,
    },
    concentracao: { hhi: 900 },
    restosResumo: {
      totalPendente: 200,
      fornecedoresAguardando: 5,
      dividaMaisAntigaAno: 2021,
      topFornecedores: [],
    },
    despesasUnidades: [],
    diariasResumo: { totalValor: 0, totalViajantes: 0, mediaReembolso: 0 },
    diariasBeneficiarios: [],
    ...overrides,
  } as unknown as RawData;
}

describe("buildDespesasViewModel", () => {
  it("classifica HHI baixo (<= 1500) como 'baixa'", () => {
    const vm = buildDespesasViewModel(makeRaw({ concentracao: { hhi: 900 } }));
    expect(vm.hhiVal).toBe(900);
    expect(vm.hhiStatusText).toContain("baixa");
  });

  it("classifica HHI moderado (1500 < hhi <= 2500) como 'moderada'", () => {
    const vm = buildDespesasViewModel(makeRaw({ concentracao: { hhi: 2000 } }));
    expect(vm.hhiStatusText).toContain("moderada");
  });

  it("classifica HHI alto (> 2500) como 'alta'", () => {
    const vm = buildDespesasViewModel(makeRaw({ concentracao: { hhi: 3000 } }));
    expect(vm.hhiStatusText).toContain("alta");
  });

  it("repassa os dados brutos para o shape final sem perder informação", () => {
    const raw = makeRaw();
    const vm = buildDespesasViewModel(raw);
    expect(vm.selectedYear).toBe(raw.context.selectedYear);
    expect(vm.isCurrentYear).toBe(raw.context.isCurrentYear);
    expect(vm.metricasGerais).toEqual(raw.metricasGerais);
    expect(vm.restosResumo).toEqual(raw.restosResumo);
  });
});
