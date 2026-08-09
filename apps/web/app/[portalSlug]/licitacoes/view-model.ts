import { getPartialYearPeriod } from "@transparencia/ui";
import type { loadLicitacoesData } from "./loader";

type LicitacoesRawData = Awaited<ReturnType<typeof loadLicitacoesData>>;

export function buildLicitacoesViewModel(raw: LicitacoesRawData) {
  const acimaLimiteGaps = raw.gaps.filter((g) => g.acimaLimite);

  const fracionamentoVendorsMap: Record<string, number> = {};
  for (const f of raw.anomalias.fracionamento) {
    fracionamentoVendorsMap[f.fornecedor] =
      (fracionamentoVendorsMap[f.fornecedor] || 0) + 1;
  }

  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    partialPeriod: getPartialYearPeriod(),
    gaps: raw.gaps,
    adesao: raw.adesao,
    adesaoExterna: raw.adesaoExterna,
    modalidades: raw.modalidades,
    acimaLimiteGaps,
    fracionamentoVendorsMap,
    numCasosFracionamento: Object.keys(fracionamentoVendorsMap).length,
  };
}
