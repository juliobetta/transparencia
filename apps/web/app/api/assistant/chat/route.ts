import { type NextRequest, NextResponse } from "next/server";
import { PostHog } from "posthog-node";
import { executeReActAgent } from "@/lib/agent/react-engine";
import { validateAndSanitizeSql } from "@/lib/sql-guardrail";

export interface AssistantMetricCard {
  title: string;
  value: string;
  badge?: string;
  variant?: "default" | "accent" | "warning" | "success";
}

export interface AssistantChartPoint {
  label: string;
  valor: number;
  formattedValue?: string;
}

export interface AssistantResponse {
  answer: string;
  metrics?: AssistantMetricCard[];
  chartData?: AssistantChartPoint[];
  chartType?: "bar" | "donut" | "metric";
  sqlQuery?: string;
}

let posthogClient: PostHog | null = null;
function trackTokenUsage(data: {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  model: string;
  portalSlug: string;
  ano: number;
  traceId?: string;
}) {
  try {
    const apiKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
    if (!apiKey) return;
    if (!posthogClient) {
      posthogClient = new PostHog(apiKey, {
        host:
          process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
      });
    }
    posthogClient.capture({
      distinctId: data.traceId || data.portalSlug || "anonymous_user",
      event: "ai_token_usage",
      properties: {
        prompt_tokens: data.promptTokens,
        completion_tokens: data.completionTokens,
        total_tokens: data.totalTokens,
        model: data.model,
        portal_slug: data.portalSlug,
        ano: data.ano,
      },
    });
  } catch (_err) {}
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      message,
      messagesHistory,
      portalSlug = "porciuncula_prefeitura",
      ano: yearParam,
      currentRoute = "/visao-geral",
      traceId,
    } = body;

    if (!message || typeof message !== "string") {
      return NextResponse.json(
        { error: "Parâmetro 'message' é obrigatório." },
        { status: 400 },
      );
    }

    const year = Number(yearParam) || 2025;

    const history = Array.isArray(messagesHistory)
      ? messagesHistory
          .filter(
            (m: {
              sender?: string;
              role?: string;
              text?: string;
              content?: string;
            }) => (m.sender || m.role) && (m.text || m.content),
          )
          .map(
            (m: {
              sender?: string;
              role?: string;
              text?: string;
              content?: string;
            }) => ({
              role: (m.role || (m.sender === "user" ? "user" : "assistant")) as
                | "user"
                | "assistant",
              content: m.content || m.text || "",
            }),
          )
      : undefined;

    // Execução Agêntica via Motor ReAct + Memória Conversacional + PostgreSQL
    const reactResult = await executeReActAgent({
      message,
      history,
      portalSlug,
      year,
      currentRoute,
      traceId,
    });

    let sanitizedQuery = reactResult.sqlQuery;
    if (reactResult.sqlQuery) {
      const guardrail = validateAndSanitizeSql(
        reactResult.sqlQuery,
        portalSlug,
      );
      if (guardrail.allowed) {
        sanitizedQuery = guardrail.sanitizedQuery;
      }
    }

    // Telemetria silenciosa de consumo de tokens
    trackTokenUsage({
      promptTokens: 150, // Estimativa do ReAct pipeline
      completionTokens: 250,
      totalTokens: 400,
      model: process.env.GEMINI_MODEL || "gemini-3.6-flash",
      portalSlug,
      ano: year,
      traceId,
    });

    return NextResponse.json({
      answer: reactResult.answer,
      metrics: reactResult.metrics,
      chartType: reactResult.chartType || "metric",
      sqlQuery: sanitizedQuery,
      chartData: reactResult.chartData,
    });
  } catch (error) {
    // biome-ignore lint/suspicious/noConsole: server error logging
    console.error("API Assistant Chat Agent Error:", error);
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "Erro interno no servidor assistente.",
      },
      { status: 500 },
    );
  }
}
