import { describe, expect, it } from "vitest";
import type { loadLicitacoesData } from "./loader";
import { buildLicitacoesViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadLicitacoesData>>;

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    portalSlug: "porciuncula_prefeitura",
    context: {
      selectedYear: 2024,
      isCurrentYear: false,
      entidadesIds: undefined,
    },
    gaps: [],
    adesao: { quantidade: 0 },
    adesaoExterna: { quantidade: 0 },
    anomalias: { fracionamento: [] },
    modalidades: [],
    ...overrides,
  } as unknown as RawData;
}

describe("buildLicitacoesViewModel", () => {
  it("filtra apenas os gaps acima do limite", () => {
    const vm = buildLicitacoesViewModel(
      makeRaw({
        gaps: [
          { acimaLimite: true, fornecedor: "A" },
          { acimaLimite: false, fornecedor: "B" },
          { acimaLimite: true, fornecedor: "C" },
        ],
      }),
    );
    expect(vm.acimaLimiteGaps).toHaveLength(2);
  });

  it("conta casos de fracionamento por fornecedor distinto", () => {
    const vm = buildLicitacoesViewModel(
      makeRaw({
        anomalias: {
          fracionamento: [
            { fornecedor: "Fornecedor X" },
            { fornecedor: "Fornecedor X" },
            { fornecedor: "Fornecedor Y" },
          ],
        },
      }),
    );
    expect(vm.numCasosFracionamento).toBe(2);
    expect(vm.fracionamentoVendorsMap).toEqual({
      "Fornecedor X": 2,
      "Fornecedor Y": 1,
    });
  });

  it("não indica fracionamento quando não há anomalias", () => {
    const vm = buildLicitacoesViewModel(makeRaw());
    expect(vm.numCasosFracionamento).toBe(0);
    expect(vm.fracionamentoVendorsMap).toEqual({});
  });
});
