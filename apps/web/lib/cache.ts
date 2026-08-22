import { unstable_cache } from "next/cache";
import posthog from "posthog-js";
import { version } from "../package.json";

/**
 * Helper para criar funções com cache de 24h versionado pelo package.json.
 *
 * - Em cada novo deploy (versão muda), a cache key expira automaticamente.
 * - Em re-extração sem novo deploy, o TTL de 24h garante atualização.
 * - Resiliente a indisponibilidades do provedor KV com fallback gracioso e reporte de $exception no PostHog.
 */
export function createCachedDataLoader<T, Args extends unknown[]>(
  fn: (...args: Args) => Promise<T>,
  keyPrefix: string,
  revalidateSeconds: number = 86400,
) {
  return async (...args: Args): Promise<T> => {
    const key = `${keyPrefix}-v${version}-${JSON.stringify(args)}`;
    try {
      const cachedFn = unstable_cache(() => fn(...args), [key], {
        revalidate: revalidateSeconds,
      });
      return await cachedFn();
    } catch (error) {
      try {
        posthog.capture("$exception", {
          error_name: "KVCacheFailure",
          error_message: error instanceof Error ? error.message : String(error),
          cache_key: key,
        });
      } catch (_phErr) {}
      // Fallback gracioso para a execução direta do DataLoader
      return await fn(...args);
    }
  };
}
