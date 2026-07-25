export const NEAR_THRESHOLD_PCT = 0.1;
export const LIMIT_COMPRAS_SERVICOS = 59906.02;
export const LIMIT_OBRAS_ENGENHARIA = 119812.02;

export function dispensationThreshold(
  numeroObra?: any,
  tipoObra?: any,
  objeto?: any,
): number {
  if (numeroObra || tipoObra) {
    return LIMIT_OBRAS_ENGENHARIA;
  }
  const objStr = String(objeto ?? "").toLowerCase();
  if (
    objStr.includes("obra") ||
    objStr.includes("engenharia") ||
    objStr.includes("reforma") ||
    objStr.includes("construcao")
  ) {
    return LIMIT_OBRAS_ENGENHARIA;
  }
  return LIMIT_COMPRAS_SERVICOS;
}
