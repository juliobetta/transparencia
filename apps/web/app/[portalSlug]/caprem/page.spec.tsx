import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadCapremData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadCapremData>>;

const { loadCapremDataMock } = vi.hoisted(() => ({
  loadCapremDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadCapremData: loadCapremDataMock,
}));

const { default: CapremPage } = await import("./page");

function makeRaw(
  overrides: { caprem?: Record<string, unknown> } & Record<
    string,
    unknown
  > = {},
): RawData {
  const { caprem: capremOverride, ...rest } = overrides;
  return {
    context: { selectedYear: 2024, isCurrentYear: false },
    caprem: {
      entidades: [],
      natureza: [],
      cadprevParcelamentos: [],
      actuarialTrend: [],
      totalEmpenhado: 1000,
      totalLiquidado: 900,
      totalPago: 800,
      taxaExecucao: 0.8,
      totalAporteAtuarial: 500,
      totalDividaResgatada: 100,
      totalCaspPlanoSaude: 0,
      actuarialRisk: {
        totalAporteExigido: 500,
        totalAporteQuitado: 400,
        romboAporteNaoRepassado: 100,
        taxaAdimplenciaAporte: 80,
        totalEmpenhadoPatronal: 300,
        totalPagoPatronal: 250,
        romboPatronalNaoRepassado: 50,
        deficitMedioMensal: 5,
        totalAmortizacaoDivida: 100,
        variacaoAmortizacaoPct: 0,
        servidoresEfetivos: 20,
        servidoresTemporariosComissionados: 2,
        razaoTemporariosEfetivosPct: 10,
      },
      ...capremOverride,
    },
    ...rest,
  } as unknown as RawData;
}

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("CapremPage", () => {
  it("happy-path: renderiza KPIs principais mesmo sem entidades/natureza", async () => {
    loadCapremDataMock.mockResolvedValue(makeRaw());

    const element = await CapremPage(props);
    render(element);

    expect(screen.getByText("Total Empenhado")).toBeInTheDocument();
    expect(screen.getByText("Índice de Adimplência")).toBeInTheDocument();
  });

  it("esconde a seção de composição contábil quando natureza está vazia", async () => {
    loadCapremDataMock.mockResolvedValue(makeRaw({ caprem: { natureza: [] } }));

    const element = await CapremPage(props);
    render(element);

    expect(
      screen.queryByText("Composição Contábil dos Repasses"),
    ).not.toBeInTheDocument();
  });

  it("exibe a seção de composição contábil quando natureza tem dados", async () => {
    loadCapremDataMock.mockResolvedValue(
      makeRaw({
        caprem: {
          natureza: [
            {
              elemento: "97",
              descricao: "Aporte",
              destino: "aporte_atuarial_caprem",
              empenhado: 100,
              pago: 90,
            },
          ],
        },
      }),
    );

    const element = await CapremPage(props);
    render(element);

    expect(
      screen.getByText("Composição Contábil dos Repasses"),
    ).toBeInTheDocument();
  });
});
