/**
 * Reporta erros de query antes de cair no fallback (lista/objeto vazio).
 *
 * As queries deste pacote usam `try { ... } catch { return [] }` para não
 * derrubar a página quando algo falha. O problema é que isso também engole
 * erros de schema (ex.: `column "orgao_nome" does not exist` após um rename
 * de mart), fazendo a página renderizar vazia sem nenhum sinal do motivo.
 *
 * Este helper registra o erro no console antes do fallback, de forma que
 * uma nova divergência de schema apareça como exceção reportada — capturável
 * por error tracking — em vez de uma tela em branco silenciosa.
 */
export function logQueryError(scope: string, error: unknown): void {
  // biome-ignore lint/suspicious/noConsole: canal de observabilidade das queries
  console.error(`[db] query "${scope}" falhou; usando fallback vazio.`, error);
}
