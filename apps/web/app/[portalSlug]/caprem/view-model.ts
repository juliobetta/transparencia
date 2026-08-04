import type { loadCapremData } from "./loader";

type CapremRawData = Awaited<ReturnType<typeof loadCapremData>>;

export function buildCapremViewModel(raw: CapremRawData) {
  const destinoMap = new Map<string, number>();
  for (const n of raw.caprem.natureza) {
    const key = n.destino;
    destinoMap.set(key, (destinoMap.get(key) || 0) + n.pago);
  }

  const destinoColors: Record<string, string> = {
    "RPPS (CAPREM)": "oklch(0.55 0.14 250)",
    "Aporte Atuarial (CAPREM)": "oklch(0.60 0.18 30)",
    "Amortização Dívida (CAPREM)": "oklch(0.55 0.15 45)",
    "INSS (RGPS)": "oklch(0.65 0.12 180)",
    "Plano de Saúde (CASP)": "oklch(0.60 0.12 210)",
    "Encargo Patronal Geral": "oklch(0.50 0.05 240)",
  };

  const naturezaChartData = Array.from(destinoMap.entries())
    .map(([dest, val]) => ({
      label: dest,
      value: val,
      barColor: destinoColors[dest] || "oklch(0.55 0.11 250)",
    }))
    .sort((a, b) => b.value - a.value);

  const naturezaCols = [
    {
      header: "Data do Lançamento",
      accessorKey: "dataEmpenho" as const,
      format: "date" as const,
    },
    { header: "Regime / Destino", accessorKey: "destino" as const },
    {
      header: "Elemento / Descrição da Natureza",
      accessorKey: "descricao" as const,
      className: "max-w-sm",
    },
    {
      header: "Empenhado",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    caprem: raw.caprem,
    naturezaCols,
    naturezaChartData,
  };
}
