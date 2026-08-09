import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadOrcamentoData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadOrcamentoData>>;

const { loadOrcamentoDataMock } = vi.hoisted(() => ({
  loadOrcamentoDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadOrcamentoData: loadOrcamentoDataMock,
}));

const { default: OrcamentoPage } = await import("./page");

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

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("OrcamentoPage", () => {
  it("happy-path: renderiza cabeçalho e KPIs de execução", async () => {
    loadOrcamentoDataMock.mockResolvedValue(makeRaw());

    const element = await OrcamentoPage(props);
    render(element);

    expect(screen.getByText("Execução Orçamentária")).toBeInTheDocument();
    expect(screen.getByText("Dotação Atualizada")).toBeInTheDocument();
  });

  it("esconde a seção 'por função' quando não há dados funcionais", async () => {
    loadOrcamentoDataMock.mockResolvedValue(makeRaw({ funcionalData: [] }));

    const element = await OrcamentoPage(props);
    render(element);

    expect(
      screen.queryByText("Para onde vai o gasto, por função"),
    ).not.toBeInTheDocument();
  });

  it("exibe a seção 'por função' quando há dados funcionais", async () => {
    loadOrcamentoDataMock.mockResolvedValue(
      makeRaw({
        funcionalData: [{ funcaoNome: "Saúde", empenhado: 100, pago: 90 }],
      }),
    );

    const element = await OrcamentoPage(props);
    render(element);

    expect(
      screen.getByText("Para onde vai o gasto, por função"),
    ).toBeInTheDocument();
  });
});
