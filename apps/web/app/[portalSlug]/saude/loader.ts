import { getHistoriaSaude } from "@transparencia/db";

export interface SaudeSearchParams {
  ano?: string;
  entidades?: string;
}

export interface SaudeContext {
  selectedYear: number;
  isCurrentYear: boolean;
}

export function parseSaudeContext(
  searchParams: SaudeSearchParams,
): SaudeContext {
  const currentYear = new Date().getFullYear();
  const selectedYear = searchParams.ano
    ? Number(searchParams.ano)
    : currentYear;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
  };
}

export async function loadSaudeData(searchParams: SaudeSearchParams) {
  const context = parseSaudeContext(searchParams);
  const saude = await getHistoriaSaude(context.selectedYear);

  return {
    context,
    saude,
  };
}
