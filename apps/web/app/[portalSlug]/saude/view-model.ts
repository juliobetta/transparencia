import { getPartialYearPeriod } from "@transparencia/ui";
import type { loadSaudeData } from "./loader";

type SaudeRawData = Awaited<ReturnType<typeof loadSaudeData>>;

export function buildSaudeViewModel(raw: SaudeRawData) {
  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    partialPeriod: getPartialYearPeriod(),
    saude: raw.saude,
  };
}
