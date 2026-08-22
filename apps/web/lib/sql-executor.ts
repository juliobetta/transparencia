import crypto from "node:crypto";
import { executeRawSql } from "@transparencia/db";
import { unstable_cache } from "next/cache";

async function runSqlQueryDirect<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  const rawRows = await executeRawSql<Record<string, unknown>>(sqlQuery);

  // Converter BigInt de volta para Number seguro se aplicável
  const sanitizedRows = rawRows.map((row) => {
    const cleanObj: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(row)) {
      if (val == null) {
        cleanObj[key] = val;
      } else if (typeof val === "bigint") {
        cleanObj[key] = Number(val);
      } else {
        cleanObj[key] = val;
      }
    }
    return cleanObj as T;
  });

  return sanitizedRows;
}

/**
 * Executa queries SQL com cache KV (unstable_cache) e fallback gracioso em caso de erro.
 * Se o serviço de cache falhar, a query executa diretamente no banco de dados PostgreSQL
 * sem interromper a resposta da aplicação.
 */
export async function executeAnalyticsQuery<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  const normalizedQuery = sqlQuery.trim().replace(/\s+/g, " ");
  // Hash SHA-256 completo para evitar colisões entre consultas SQL longas
  const hash = crypto
    .createHash("sha256")
    .update(normalizedQuery)
    .digest("hex");
  const cacheKey = `sql-query-${hash}`;

  try {
    const cachedFn = unstable_cache(
      () => runSqlQueryDirect<T>(sqlQuery),
      [cacheKey],
      { revalidate: 86400 }, // TTL de 24h
    );
    return await cachedFn();
  } catch (_error) {
    // Fallback gracioso para a execução direta no banco PostgreSQL
    return await runSqlQueryDirect<T>(sqlQuery);
  }
}
