import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { loadDespesasData } from "./loader";

type RawData = Awaited<ReturnType<typeof loadDespesasData>>;

const { loadDespesasDataMock } = vi.hoisted(() => ({
  loadDespesasDataMock: vi.fn(),
}));

vi.mock("./loader", () => ({
  loadDespesasData: loadDespesasDataMock,
}));

const { default: DespesasPage } = await import("./page");

function makeRaw(overrides: Record<string, unknown> = {}): RawData {
  return {
    context: {
      selectedYear: 2024,
      isCurrentYear: false,
      entidadesIds: undefined,
    },
    metricasGerais: {
      empenhado: 1_000_000,
      liquidado: 800_000,
      pago: 700_000,
      taxaLiquidacao: 80,
      taxaPagamento: 70,
    },
    impactoLocais: {
      localPago: 600_000,
      externoPago: 100_000,
      pctLocal: 85.7,
      historicoPctLocal: 80,
    },
    concentracao: { hhi: 900 },
    restosResumo: {
      totalPendente: 200_000,
      fornecedoresAguardando: 5,
      dividaMaisAntigaAno: 2021,
      topFornecedores: [],
    },
    despesasUnidades: [],
    diariasResumo: { totalValor: 0, totalViajantes: 0, mediaReembolso: 0 },
    diariasBeneficiarios: [],
    ...overrides,
  } as unknown as RawData;
}

const props = {
  params: Promise.resolve({ portalSlug: "porciuncula_prefeitura" }),
  searchParams: Promise.resolve({}),
};

describe("DespesasPage", () => {
  it("happy-path: renderiza KPIs principais com dados completos", async () => {
    loadDespesasDataMock.mockResolvedValue(makeRaw());

    const element = await DespesasPage(props);
    render(element);

    expect(screen.getByText("Despesas Detalhadas")).toBeInTheDocument();
    expect(screen.getByText("Total empenhado")).toBeInTheDocument();
    expect(screen.getByText("Restos a pagar pendentes")).toBeInTheDocument();
  });

  it("esconde seções condicionais quando as listas vêm vazias", async () => {
    loadDespesasDataMock.mockResolvedValue(makeRaw());

    const element = await DespesasPage(props);
    render(element);

    // despesasUnidades, diariasBeneficiarios e topFornecedores vazios -> blocos não renderizam
    expect(
      screen.queryByText("Principais servidores beneficiários de diárias"),
    ).not.toBeInTheDocument();
  });

  it("exibe seções condicionais quando os dados vêm populados", async () => {
    loadDespesasDataMock.mockResolvedValue(
      makeRaw({
        despesasUnidades: [
          { unidade: "Saúde", empenhado: 100, liquidado: 90, pago: 80 },
        ],
        diariasBeneficiarios: [
          { favorecido: "Fulano de Tal", cargo: "Motorista", valor: 500 },
        ],
        restosResumo: {
          totalPendente: 200_000,
          fornecedoresAguardando: 5,
          dividaMaisAntigaAno: 2021,
          topFornecedores: [{ fornecedor: "Fornecedor X", valor: 1000 }],
        },
      }),
    );

    const element = await DespesasPage(props);
    render(element);

    expect(
      screen.getByText("Principais servidores beneficiários de diárias"),
    ).toBeInTheDocument();
  });
});
