import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadPessoalData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadPessoalData>>;

const { loadPessoalDataMock } = vi.hoisted(() => ({
  loadPessoalDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadPessoalData: loadPessoalDataMock,
}));

const { default: PessoalPage } = await import("./page");

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

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("PessoalPage", () => {
  it("happy-path: renderiza cabeçalho e KPIs principais", async () => {
    loadPessoalDataMock.mockResolvedValue(makeRaw());

    const element = await PessoalPage(props);
    render(element);

    expect(screen.getByText("Folha de Pagamento")).toBeInTheDocument();
    expect(
      screen.getByText("Efetivos no comando das chefias"),
    ).toBeInTheDocument();
  });

  it("exibe o card de 13º salário quando decimo13 está disponível", async () => {
    loadPessoalDataMock.mockResolvedValue(makeRaw());

    const element = await PessoalPage(props);
    render(element);

    expect(
      screen.queryByText(/Sem dados de 13º salário/),
    ).not.toBeInTheDocument();
  });

  it("exibe mensagem de fallback quando decimo13 é null", async () => {
    loadPessoalDataMock.mockResolvedValue(makeRaw({ decimo13: null }));

    const element = await PessoalPage(props);
    render(element);

    expect(screen.getByText(/Sem dados de 13º salário/)).toBeInTheDocument();
  });

  it("mostra 'N/D' quando pctChefias é null", async () => {
    loadPessoalDataMock.mockResolvedValue(makeRaw({ pctChefias: null }));

    const element = await PessoalPage(props);
    render(element);

    expect(screen.getByText("N/D")).toBeInTheDocument();
  });
});
