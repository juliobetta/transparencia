import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadSaudeData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadSaudeData>>;

const { loadSaudeDataMock } = vi.hoisted(() => ({
  loadSaudeDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadSaudeData: loadSaudeDataMock,
}));

const { default: SaudePage } = await import("./page");

function makeRaw(
  overrides: { saude?: Record<string, unknown> } & Record<string, unknown> = {},
): RawData {
  const { saude: saudeOverride, ...rest } = overrides;
  const { orcamento: orcamentoOverride, ...saudeRest } = saudeOverride ?? {};
  return {
    portalSlug: "porciuncula_prefeitura",
    context: { selectedYear: 2024, isCurrentYear: false },
    saude: {
      orcamento: {
        dotacao: 1000,
        empenhado: 800,
        liquidado: 700,
        pago: 600,
        taxaExecucao: 0.8,
        alertaSubExecucao: false,
        medicamentosInsumos: 100,
        medicamentosInsumosPago: 90,
        judicializacao: 20,
        judicializacaoPago: 15,
        contratosVinculadosCount: 5,
        fornecedoresAtivosCount: 10,
        ...(orcamentoOverride as Record<string, unknown> | undefined),
      },
      farmaceutica: {
        medicamentosInsumos: 100,
        medicamentosInsumosPago: 90,
        judicializacao: 20,
        judicializacaoPago: 15,
        hhi: 900,
        hhiClassificacao: "baixa",
      },
      fontesReceita: {
        repassesPrefeitura: 500,
        emendasParlamentares: 50,
      },
      executionTrend: [],
      licitacoesSaude: {
        adesaoCaronaCount: 0,
        adesaoCaronaValor: 0,
        empenhosAtaExternaCount: 0,
        pagoAtaExternaValor: 0,
        modalidades: [],
      },
      emendasStats: { lista: [], totalAutorizado: 50 },
      emendas: [],
      emendasTotal: 50,
      ...saudeRest,
    },
    ...rest,
  } as unknown as RawData;
}

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("SaudePage", () => {
  it("happy-path: renderiza cabeçalho e KPIs principais", async () => {
    loadSaudeDataMock.mockResolvedValue(makeRaw());

    const element = await SaudePage(props);
    render(element);

    expect(screen.getByText("Dotação Atualizada")).toBeInTheDocument();
    expect(screen.getByText("Concentração (HHI)")).toBeInTheDocument();
  });

  it("não exibe alerta de subexecução quando alertaSubExecucao é falso", async () => {
    loadSaudeDataMock.mockResolvedValue(
      makeRaw({ saude: { orcamento: { alertaSubExecucao: false } } }),
    );

    const element = await SaudePage(props);
    render(element);

    expect(
      screen.queryByText("Alerta de Subexecução Orçamentária"),
    ).not.toBeInTheDocument();
  });

  it("exibe alerta de subexecução quando o orçamento ficou abaixo de 70%", async () => {
    loadSaudeDataMock.mockResolvedValue(
      makeRaw({ saude: { orcamento: { alertaSubExecucao: true } } }),
    );

    const element = await SaudePage(props);
    render(element);

    expect(
      screen.getByText("Alerta de Subexecução Orçamentária"),
    ).toBeInTheDocument();
  });
});
