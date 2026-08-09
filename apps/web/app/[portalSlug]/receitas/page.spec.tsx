import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadReceitasData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadReceitasData>>;

const { loadReceitasDataMock } = vi.hoisted(() => ({
  loadReceitasDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadReceitasData: loadReceitasDataMock,
}));

const { default: ReceitasPage } = await import("./page");

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

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("ReceitasPage", () => {
  it("happy-path: renderiza cabeçalho e totais principais", async () => {
    loadReceitasDataMock.mockResolvedValue(makeRaw());

    const element = await ReceitasPage(props);
    render(element);

    expect(screen.getByText("Fontes de Receita")).toBeInTheDocument();
    expect(screen.getByText("Total Arrecadado Real")).toBeInTheDocument();
  });

  it("não exibe o alerta de dependência quando alertaDependencia é falso", async () => {
    loadReceitasDataMock.mockResolvedValue(
      makeRaw({ fonte: makeFonte({ alertaDependencia: false }) }),
    );

    const element = await ReceitasPage(props);
    render(element);

    expect(
      screen.queryByText(/Alta Dependência de Transferências Externas/),
    ).not.toBeInTheDocument();
  });

  it("exibe o alerta de vulnerabilidade fiscal quando alertaDependencia é verdadeiro", async () => {
    loadReceitasDataMock.mockResolvedValue(
      makeRaw({
        fonte: makeFonte({ alertaDependencia: true, pctPropria: 12 }),
      }),
    );

    const element = await ReceitasPage(props);
    render(element);

    expect(
      screen.getByText(/Alta Dependência de Transferências Externas/),
    ).toBeInTheDocument();
  });

  it("não quebra quando não há fonte de receita disponível (loader retorna undefined)", async () => {
    loadReceitasDataMock.mockResolvedValue(makeRaw({ fonte: undefined }));

    const element = await ReceitasPage(props);
    render(element);

    expect(screen.getByText("Fontes de Receita")).toBeInTheDocument();
  });
});
