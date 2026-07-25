export function fmtCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

export function fmtCompact(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) {
    return `R$ ${(value / 1_000_000_000).toFixed(1)}bi`;
  }
  if (abs >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)}mi`;
  }
  if (abs >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(1)}mil`;
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(value);
}

export function fmtPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export function fmtNumber(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function fmtDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "--/--/----";
  const cleanStr = dateStr.split("T")[0];
  const parts = cleanStr.split("-");
  if (parts.length === 3 && parts[0].length === 4) {
    const [year, month, day] = parts;
    return `${day}/${month}/${year}`;
  }
  return dateStr;
}
