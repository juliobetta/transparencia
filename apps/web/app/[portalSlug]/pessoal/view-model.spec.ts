import { describe, expect, it } from "vitest";
import type { loadPessoalData } from "./loader";
import { buildPessoalViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadPessoalData>>;

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    context: {
      selectedYear: 2024,
      isCurrentYear: false,
      entidadesIds: undefined,
    },
    folhaData: [
      { totalFolha: 1000, totalPago: 900, rclProxy: 2000, percentualFolha: 45 },
    ],
    pctChefias: 60,
    decimo13: { empenhado: 100, pago: 90, pctPago: 90 },
    distribuicaoProventos: [],
    departmentalPayroll: [],
    ...overrides,
  } as unknown as RawData;
}

describe("buildPessoalViewModel", () => {
  it("usa a primeira linha de folhaData como currentYearRow", () => {
    const vm = buildPessoalViewModel(makeRaw());
    expect(vm.currentYearRow.percentualFolha).toBe(45);
  });

  it("usa valores zerados quando folhaData vem vazio", () => {
    const vm = buildPessoalViewModel(makeRaw({ folhaData: [] }));
    expect(vm.currentYearRow).toEqual({
      totalFolha: 0,
      totalPago: 0,
      rclProxy: 0,
      percentualFolha: 0,
    });
  });

  it("repassa pctChefias e decimo13 sem transformação", () => {
    const vm = buildPessoalViewModel(
      makeRaw({ pctChefias: null, decimo13: null }),
    );
    expect(vm.pctChefias).toBeNull();
    expect(vm.decimo13).toBeNull();
  });
});
