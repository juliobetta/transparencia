import { unstable_cache } from "next/cache";
import { version } from "../package.json";

/**
 * Helper para criar funções com cache de 24h versionado pelo package.json.
 *
 * - Em cada novo deploy (versao muda), a cache key expira automaticamente.
 * - Em re-extração sem novo deploy, o TTL de 24h garante atualização.
 */
export function createCachedDataLoader<T, Args extends any[]>(
  fn: (...args: Args) => Promise<T>,
  keyPrefix: string,
  revalidateSeconds: number = 86400,
) {
  return (...args: Args): Promise<T> => {
    const key = `${keyPrefix}-v${version}-${JSON.stringify(args)}`;
    const cachedFn = unstable_cache(() => fn(...args), [key], {
      revalidate: revalidateSeconds,
    });
    return cachedFn();
  };
}
