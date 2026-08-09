import { getPartialYearPeriod } from "@transparencia/ui";
import type { loadDespesasData } from "./loader";

type DespesasRawData = Awaited<ReturnType<typeof loadDespesasData>>;

export function buildDespesasViewModel(raw: DespesasRawData) {
  const hhiVal = Math.round(raw.concentracao.hhi || 0);
  const hhiStatusText =
    hhiVal <= 1500
      ? "baixa · abaixo de 1.500"
      : hhiVal <= 2500
        ? "moderada · abaixo de 2.500"
        : "alta · acima de 2.500";

  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    partialPeriod: getPartialYearPeriod(),
    metricasGerais: raw.metricasGerais,
    impactoLocais: raw.impactoLocais,
    restosResumo: raw.restosResumo,
    despesasUnidades: raw.despesasUnidades,
    diariasResumo: raw.diariasResumo,
    diariasBeneficiarios: raw.diariasBeneficiarios,
    hhiVal,
    hhiStatusText,
  };
}
