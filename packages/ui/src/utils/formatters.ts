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

export function fmtPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value))
    return "0,00%";
  return `${value.toFixed(2)}%`;
}

export function fmtNumber(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function fmtDate(val: string | Date | null | undefined): string {
  if (!val) return "--/--/----";
  if (val instanceof Date) {
    if (Number.isNaN(val.getTime())) return "--/--/----";
    const dd = String(val.getUTCDate()).padStart(2, "0");
    const mm = String(val.getUTCMonth() + 1).padStart(2, "0");
    const yyyy = val.getUTCFullYear();
    return `${dd}/${mm}/${yyyy}`;
  }
  const dateStr = String(val).trim();
  const isoMatch = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (isoMatch) {
    return `${isoMatch[3]}/${isoMatch[2]}/${isoMatch[1]}`;
  }
  const brMatch = dateStr.match(/^(\d{2})\/(\d{2})\/(\d{4})/);
  if (brMatch) {
    return `${brMatch[1]}/${brMatch[2]}/${brMatch[3]}`;
  }
  const parsed = new Date(dateStr);
  if (!Number.isNaN(parsed.getTime())) {
    const dd = String(parsed.getUTCDate()).padStart(2, "0");
    const mm = String(parsed.getUTCMonth() + 1).padStart(2, "0");
    const yyyy = parsed.getUTCFullYear();
    return `${dd}/${mm}/${yyyy}`;
  }
  return dateStr;
}

export function fmtLicitacaoModalidade(
  modalidade: string | null | undefined,
): string {
  const MODALIDADE_LABELS: Record<string, string> = {
    adesao_ata_interna: "Adesão a Ata (Carona Interna)",
    adesao_ata_externa: "Adesão a Ata (Externa)",
    sem_licitacao: "Sem Licitação",
    gap_licitacao: "Sem Licitação",
    licitacao_propria: "Licitação Própria",
    outros: "Outros",
  };

  if (!modalidade?.trim()) return "Outros";
  const clean = modalidade.trim().toLowerCase();
  if (MODALIDADE_LABELS[clean]) {
    return MODALIDADE_LABELS[clean];
  }
  return clean
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function getPartialYearPeriod(referenceDate = new Date()): string {
  if (!referenceDate || Number.isNaN(referenceDate.getTime())) return "";
  const currentMonthIndex = referenceDate.getMonth();
  const prevMonthIndex = currentMonthIndex > 0 ? currentMonthIndex - 1 : 0;
  const year = referenceDate.getFullYear();

  const formatter = new Intl.DateTimeFormat("pt-BR", { month: "short" });

  const formatMonth = (monthIndex: number) => {
    const raw = formatter
      .format(new Date(year, monthIndex, 1))
      .replace(".", "");
    return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
  };

  const jan = formatMonth(0);
  if (prevMonthIndex === 0) return jan;

  const prev = formatMonth(prevMonthIndex);
  return `${jan}–${prev}`;
}
