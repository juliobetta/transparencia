import { getPartialYearPeriod } from "@transparencia/ui";
import type { loadPessoalData } from "./loader";

type PessoalRawData = Awaited<ReturnType<typeof loadPessoalData>>;

export function buildPessoalViewModel(raw: PessoalRawData) {
  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    partialPeriod: getPartialYearPeriod(),
    pctChefias: raw.pctChefias,
    decimo13: raw.decimo13,
    distribuicaoProventos: raw.distribuicaoProventos,
    departmentalPayroll: raw.departmentalPayroll,
    currentYearRow: raw.folhaData[0] || {
      totalFolha: 0,
      totalPago: 0,
      rclProxy: 0,
      percentualFolha: 0,
    },
  };
}
