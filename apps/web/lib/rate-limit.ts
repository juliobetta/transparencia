export interface RateLimitResult {
  success: boolean;
  limit: number;
  remaining: number;
  resetAt: number;
  isAuth: boolean;
}

interface RateLimitEntry {
  timestamps: number[];
}

const rateLimitStore = new Map<string, RateLimitEntry>();
const WINDOW_MS = 24 * 60 * 60 * 1000; // 24 Horas
function getAnonymousLimit(): number {
  const envVal = process.env.AI_ANONYMOUS_DAILY_LIMIT;
  if (envVal != null && !Number.isNaN(Number(envVal))) {
    return Number(envVal);
  }
  return 5;
}

export function checkAnonymousRateLimit(
  req: Request,
  overrideMaxRequests?: number,
): RateLimitResult {
  const maxRequests = overrideMaxRequests ?? getAnonymousLimit();
  // 1. Verificar se a requisição possui credencial de usuário ou chave de API (bypassa limite anônimo)
  const authHeader = req.headers.get("authorization");
  const apiKeyHeader = req.headers.get("x-mcp-api-key");

  if (authHeader || apiKeyHeader) {
    return {
      success: true,
      limit: Infinity,
      remaining: Infinity,
      resetAt: 0,
      isAuth: true,
    };
  }

  // 2. Extrair IP do cliente a partir dos cabeçalhos Vercel / Proxy
  const forwardedFor = req.headers.get("x-forwarded-for");
  const clientIp =
    forwardedFor?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "127.0.0.1";

  const key = `anon:${clientIp}`;
  const now = Date.now();
  const entry = rateLimitStore.get(key) || { timestamps: [] };

  // Filtrar apenas timestamps dentro da janela de 24h
  entry.timestamps = entry.timestamps.filter((t) => now - t < WINDOW_MS);

  if (entry.timestamps.length >= maxRequests) {
    const oldestTimestamp = entry.timestamps[0] || now;
    const resetAt = oldestTimestamp + WINDOW_MS;

    return {
      success: false,
      limit: maxRequests,
      remaining: 0,
      resetAt,
      isAuth: false,
    };
  }

  // Registrar requisição atual
  entry.timestamps.push(now);
  rateLimitStore.set(key, entry);

  const remaining = Math.max(0, maxRequests - entry.timestamps.length);
  const resetAt = now + WINDOW_MS;

  return {
    success: true,
    limit: maxRequests,
    remaining,
    resetAt,
    isAuth: false,
  };
}

export function resetRateLimitStore(): void {
  rateLimitStore.clear();
}
