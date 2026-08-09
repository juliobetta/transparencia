import { describe, expect, it } from "vitest";
import type { loadSaudeData } from "./loader";
import { buildSaudeViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadSaudeData>>;

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    portalSlug: "porciuncula_prefeitura",
    context: { selectedYear: 2024, isCurrentYear: false },
    saude: {
      orcamento: { dotacao: 0, empenhado: 0 },
      farmaceutica: { hhi: 0, hhiClassificacao: "baixa" },
      fontesReceita: {},
      executionTrend: [],
      licitacoesSaude: [],
      emendasStats: { lista: [], totalAutorizado: 0 },
      emendas: [],
      emendasTotal: 0,
    },
    ...overrides,
  } as unknown as RawData;
}

describe("buildSaudeViewModel", () => {
  it("repassa o objeto saude computado pelo loader sem transformação", () => {
    const raw = makeRaw();
    const vm = buildSaudeViewModel(raw);
    expect(vm.saude).toBe(raw.saude);
    expect(vm.selectedYear).toBe(raw.context.selectedYear);
  });
});
