import { beforeEach, describe, expect, it } from "vitest";
import { checkAnonymousRateLimit, resetRateLimitStore } from "../rate-limit";

describe("rate-limit utility", () => {
  beforeEach(() => {
    resetRateLimitStore();
  });

  it("permite requisições de usuários anônimos até o limite máximo de 5", () => {
    const req = new Request("http://localhost:3000/api/assistant/chat", {
      headers: { "x-forwarded-for": "203.0.113.1" },
    });

    for (let i = 1; i <= 5; i++) {
      const result = checkAnonymousRateLimit(req, 5);
      expect(result.success).toBe(true);
      expect(result.remaining).toBe(5 - i);
      expect(result.isAuth).toBe(false);
    }
  });

  it("bloqueia a 6ª requisição do mesmo IP anônimo com status de sucesso falso", () => {
    const req = new Request("http://localhost:3000/api/assistant/chat", {
      headers: { "x-forwarded-for": "203.0.113.2" },
    });

    for (let i = 1; i <= 5; i++) {
      checkAnonymousRateLimit(req, 5);
    }

    const blockedResult = checkAnonymousRateLimit(req, 5);
    expect(blockedResult.success).toBe(false);
    expect(blockedResult.remaining).toBe(0);
    expect(blockedResult.resetAt).toBeGreaterThan(Date.now());
  });

  it("permite acesso ilimitado quando o cabeçalho Authorization ou X-MCP-API-Key está presente", () => {
    const reqWithAuth = new Request("http://localhost:3000/api/mcp", {
      headers: {
        "x-forwarded-for": "203.0.113.3",
        Authorization: "Bearer valid-token",
      },
    });

    for (let i = 1; i <= 10; i++) {
      const result = checkAnonymousRateLimit(reqWithAuth, 5);
      expect(result.success).toBe(true);
      expect(result.isAuth).toBe(true);
    }

    const reqWithApiKey = new Request("http://localhost:3000/api/mcp", {
      headers: {
        "x-forwarded-for": "203.0.113.3",
        "x-mcp-api-key": "secret-api-key",
      },
    });

    const apiKeyResult = checkAnonymousRateLimit(reqWithApiKey, 5);
    expect(apiKeyResult.success).toBe(true);
    expect(apiKeyResult.isAuth).toBe(true);
  });

  it("respeita o limite configurado via variável de ambiente AI_ANONYMOUS_DAILY_LIMIT", () => {
    process.env.AI_ANONYMOUS_DAILY_LIMIT = "2";
    const req = new Request("http://localhost:3000/api/assistant/chat", {
      headers: { "x-forwarded-for": "203.0.113.10" },
    });

    expect(checkAnonymousRateLimit(req).success).toBe(true);
    expect(checkAnonymousRateLimit(req).success).toBe(true);
    expect(checkAnonymousRateLimit(req).success).toBe(false);

    delete process.env.AI_ANONYMOUS_DAILY_LIMIT;
  });
});
