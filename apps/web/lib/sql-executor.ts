import crypto from "node:crypto";
import { executeRawSql } from "@transparencia/db";
import { kv } from "./kv";

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
 * Executa queries SQL com cache KV (Redis) e fallback gracioso para execução direta no Postgres.
 * Grava e lê do cliente KV unificado (redis.get / redis.set) com TTL de 24h.
 */
export async function executeAnalyticsQuery<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  const normalizedQuery = sqlQuery.trim().replace(/\s+/g, " ");
  // Hash SHA-256 para chave de cache no Redis
  const hash = crypto
    .createHash("sha256")
    .update(normalizedQuery)
    .digest("hex");
  const cacheKey = `sql-query-${hash}`;

  // 1. Tentar obter do Redis local / Vercel KV
  try {
    const cachedRows = await kv.get<T[]>(cacheKey);
    if (cachedRows && Array.isArray(cachedRows)) {
      return cachedRows;
    }
  } catch (_err) {
    // Falha de conexão com o KV ignora e prossegue para a busca no Postgres
  }

  // 2. Consulta direta ao banco de dados PostgreSQL
  const rows = await runSqlQueryDirect<T>(sqlQuery);

  // 3. Gravar resultado no Redis com TTL de 24h (86400s)
  try {
    await kv.set(cacheKey, rows, { ttlSeconds: 86400 });
  } catch (_err) {
    // Falha na gravação do KV ignora sem interromper a resposta
  }

  return rows;
}
