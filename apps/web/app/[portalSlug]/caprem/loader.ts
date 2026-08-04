import { getHistoriaCaprem } from "@transparencia/db";

export interface CapremSearchParams {
  ano?: string;
  empresa?: string;
}

export interface CapremContext {
  selectedYear: number;
  isCurrentYear: boolean;
}

export function parseCapremContext(
  searchParams: CapremSearchParams,
): CapremContext {
  const currentYear = new Date().getFullYear();
  const selectedYear = searchParams.ano
    ? Number(searchParams.ano)
    : currentYear;

  return {
    selectedYear,
    isCurrentYear: selectedYear === currentYear,
  };
}

export async function loadCapremData(
  portalSlug: string,
  searchParams: CapremSearchParams,
) {
  const context = parseCapremContext(searchParams);
  const caprem = await getHistoriaCaprem(
    portalSlug,
    context.selectedYear,
    null,
  );

  return {
    context,
    caprem,
  };
}
