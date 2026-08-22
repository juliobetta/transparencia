import Redis from "ioredis";
import posthog from "posthog-js";

/**
 * Cliente KV / Redis unificado utilizando ioredis.
 *
 * - Em Localhost: Conecta via process.env.REDIS_URL ("redis://localhost:6379") do Docker.
 * - Em Produção (Official Redis for Vercel / Redis Cloud): Conecta via process.env.REDIS_URL / process.env.KV_URL.
 */
const redisUrl =
  process.env.REDIS_URL || process.env.KV_URL || "redis://localhost:6379";

function createRedisClient(): Redis {
  const client = new Redis(redisUrl, {
    maxRetriesPerRequest: 3,
    lazyConnect: true,
    enableOfflineQueue: false,
    retryStrategy(times) {
      if (times > 3) return null; // Encerra retentativas após 3 falhas
      return Math.min(times * 100, 2000);
    },
  });

  client.on("error", (err) => {
    try {
      posthog.capture("$exception", {
        error_name: "RedisClientError",
        error_message: err instanceof Error ? err.message : String(err),
      });
    } catch (_phErr) {}
  });

  return client;
}

// Singleton global para reuso de conexão no ambiente Serverless Node.js
const globalForRedis = globalThis as unknown as { redisClient?: Redis };
export const redis = globalForRedis.redisClient ?? createRedisClient();

if (process.env.NODE_ENV !== "production") {
  globalForRedis.redisClient = redis;
}

export interface KvClient {
  get<T>(key: string): Promise<T | null>;
  set(
    key: string,
    value: unknown,
    options?: { ttlSeconds?: number },
  ): Promise<void>;
  del(key: string): Promise<void>;
}

export const kv: KvClient = {
  async get<T>(key: string): Promise<T | null> {
    try {
      const data = await redis.get(key);
      if (!data) return null;
      return JSON.parse(data) as T;
    } catch (_err) {
      return null;
    }
  },

  async set(
    key: string,
    value: unknown,
    options?: { ttlSeconds?: number },
  ): Promise<void> {
    try {
      const stringified = JSON.stringify(value);
      if (options?.ttlSeconds) {
        await redis.set(key, stringified, "EX", options.ttlSeconds);
      } else {
        await redis.set(key, stringified);
      }
    } catch (_err) {}
  },

  async del(key: string): Promise<void> {
    try {
      await redis.del(key);
    } catch (_err) {}
  },
};
