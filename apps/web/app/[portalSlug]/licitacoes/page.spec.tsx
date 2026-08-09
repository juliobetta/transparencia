import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadLicitacoesData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadLicitacoesData>>;

const { loadLicitacoesDataMock } = vi.hoisted(() => ({
  loadLicitacoesDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadLicitacoesData: loadLicitacoesDataMock,
}));

const { default: LicitacoesPage } = await import("./page");

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

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("LicitacoesPage", () => {
  it("happy-path: renderiza cabeçalho e KPIs com dados vazios (sem crash)", async () => {
    loadLicitacoesDataMock.mockResolvedValue(makeRaw());

    const element = await LicitacoesPage(props);
    render(element);

    expect(screen.getByText("Licitações e Contratos")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Nenhuma informação de modalidade disponível para o período.",
      ),
    ).toBeInTheDocument();
  });

  it("não exibe alerta de fracionamento quando não há casos", async () => {
    loadLicitacoesDataMock.mockResolvedValue(makeRaw());

    const element = await LicitacoesPage(props);
    render(element);

    expect(screen.queryByText(/de possível/)).not.toBeInTheDocument();
  });

  it("exibe alerta de fracionamento e gráfico de modalidades quando há dados", async () => {
    loadLicitacoesDataMock.mockResolvedValue(
      makeRaw({
        gaps: [
          {
            acimaLimite: true,
            fornecedor: "Fornecedor X",
            valorContrato: 100000,
            periodo: "01/2024",
          },
        ],
        anomalias: {
          fracionamento: [
            { fornecedor: "Fornecedor X" },
            { fornecedor: "Fornecedor X" },
            { fornecedor: "Fornecedor X" },
          ],
        },
        modalidades: [
          {
            modalidade: "Pregão",
            valorTotal: 1000,
            quantidade: 3,
            percentual_valor: 100,
            pctValor: 100,
          },
        ],
      }),
    );

    const element = await LicitacoesPage(props);
    render(element);

    expect(screen.getByText(/1 caso de possível/)).toBeInTheDocument();
    expect(
      screen.queryByText(
        "Nenhuma informação de modalidade disponível para o período.",
      ),
    ).not.toBeInTheDocument();
  });
});
