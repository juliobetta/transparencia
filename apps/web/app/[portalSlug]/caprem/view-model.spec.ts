import { describe, expect, it } from "vitest";
import type { loadCapremData } from "./loader";
import { buildCapremViewModel } from "./view-model";

type RawData = Awaited<ReturnType<typeof loadCapremData>>;

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
      totalEmpenhado: 0,
      totalLiquidado: 0,
      totalPago: 0,
      taxaExecucao: 0,
      totalAporteAtuarial: 0,
      totalDividaResgatada: 0,
      totalCaspPlanoSaude: 0,
      actuarialRisk: {
        totalAporteExigido: 0,
        totalAporteQuitado: 0,
        romboAporteNaoRepassado: 0,
        taxaAdimplenciaAporte: 100,
        totalEmpenhadoPatronal: 0,
        totalPagoPatronal: 0,
        romboPatronalNaoRepassado: 0,
        deficitMedioMensal: 0,
        totalAmortizacaoDivida: 0,
        variacaoAmortizacaoPct: 0,
        servidoresEfetivos: 0,
        servidoresTemporariosComissionados: 0,
        razaoTemporariosEfetivosPct: 0,
      },
      ...capremOverride,
    },
    ...rest,
  } as unknown as RawData;
}

describe("buildCapremViewModel", () => {
  it("traduz destino conhecido para o rótulo amigável", () => {
    const vm = buildCapremViewModel(
      makeRaw({
        caprem: {
          natureza: [
            {
              elemento: "97",
              descricao: "Aporte",
              destino: "aporte_atuarial_caprem",
              empenhado: 100,
              pago: 100,
            },
          ],
        },
      }),
    );
    expect(vm.caprem.natureza[0].destino).toBe("Aporte Atuarial (CAPREM)");
  });

  it("mantém a chave original quando o destino é desconhecido", () => {
    const vm = buildCapremViewModel(
      makeRaw({
        caprem: {
          natureza: [
            {
              elemento: "1",
              descricao: "X",
              destino: "destino_nao_mapeado",
              empenhado: 10,
              pago: 10,
            },
          ],
        },
      }),
    );
    expect(vm.caprem.natureza[0].destino).toBe("destino_nao_mapeado");
  });

  it("agrega naturezaChartData por destino somando pago, ordenado desc", () => {
    const vm = buildCapremViewModel(
      makeRaw({
        caprem: {
          natureza: [
            {
              elemento: "97",
              descricao: "A",
              destino: "aporte_atuarial_caprem",
              empenhado: 10,
              pago: 100,
            },
            {
              elemento: "97",
              descricao: "B",
              destino: "aporte_atuarial_caprem",
              empenhado: 10,
              pago: 50,
            },
            {
              elemento: "71",
              descricao: "C",
              destino: "amortizacao_divida_caprem",
              empenhado: 10,
              pago: 200,
            },
          ],
        },
      }),
    );

    expect(vm.naturezaChartData).toEqual([
      {
        label: "Amortização Dívida (CAPREM)",
        value: 200,
        barColor: expect.any(String),
      },
      {
        label: "Aporte Atuarial (CAPREM)",
        value: 150,
        barColor: expect.any(String),
      },
    ]);
  });
});
