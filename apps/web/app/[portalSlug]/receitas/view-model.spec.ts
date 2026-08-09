import { describe, expect, it } from "vitest";
import type { loadReceitasData } from "./loader";
import { buildReceitasViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadReceitasData>>;

function makeFonte(overrides: Record<string, unknown> = {}) {
  return {
    receitaPropriaPrevisto: 1000,
    receitaPropriaArrecadado: 900,
    transferenciasUniaoPrevisto: 500,
    transferenciasUniaoArrecadado: 400,
    transferenciasEstadoPrevisto: 300,
    transferenciasEstadoArrecadado: 200,
    receitaExtraOrcamentariaArrecadado: 50,
    totalPrevisto: 1800,
    totalArrecadado: 1550,
    pctPropria: 58,
    pctArrecadado: 0.86,
    alertaDependencia: false,
    totalPctChange: 5,
    emendasTotalArrecadado: 0,
    emendasPixArrecadado: 0,
    emendasIndividuaisArrecadado: 0,
    fpmArrecadado: 0,
    icmsArrecadado: 0,
    issIptuArrecadado: 0,
    ...overrides,
  };
}

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    portalSlug: "porciuncula_prefeitura",
    context: {
      selectedYear: 2024,
      isCurrentYear: false,
      entidadesIds: undefined,
    },
    fonte: makeFonte(),
    ...overrides,
  } as unknown as RawData;
}

describe("buildReceitasViewModel", () => {
  it("usa valores zerados quando não há fonte de receita disponível", () => {
    const vm = buildReceitasViewModel(makeRaw({ fonte: undefined }));
    expect(vm.totalArr).toBe(0);
    expect(vm.totalPrev).toBe(0);
    expect(vm.rec.alertaDependencia).toBe(false);
  });

  it("formata a variação como alta (▲) quando totalPctChange é positivo", () => {
    const vm = buildReceitasViewModel(
      makeRaw({ fonte: makeFonte({ totalPctChange: 12.3 }) }),
    );
    expect(vm.variationText).toContain("▲");
    expect(vm.variationText).toContain("12,3%");
  });

  it("formata a variação como queda (▼) quando totalPctChange é negativo", () => {
    const vm = buildReceitasViewModel(
      makeRaw({ fonte: makeFonte({ totalPctChange: -8 }) }),
    );
    expect(vm.variationText).toContain("▼");
    expect(vm.variationText).toContain("8,0%");
  });

  it("mostra 'Orçamento aprovado' quando não há ano anterior para comparar", () => {
    const vm = buildReceitasViewModel(
      makeRaw({ fonte: makeFonte({ totalPctChange: null }) }),
    );
    expect(vm.variationText).toBe("Orçamento aprovado");
  });

  it("calcula pctRealizado como 0 quando o previsto é 0 (evita divisão por zero)", () => {
    const vm = buildReceitasViewModel(
      makeRaw({
        fonte: makeFonte({
          transferenciasUniaoPrevisto: 0,
          transferenciasUniaoArrecadado: 0,
        }),
      }),
    );
    const transferenciasUniao = vm.origensData.find(
      (o) => o.fonte === "Transferências da União",
    );
    expect(transferenciasUniao?.pctRealizado).toBe(0);
  });
});
