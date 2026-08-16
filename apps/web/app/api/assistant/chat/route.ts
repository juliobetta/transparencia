import { type NextRequest, NextResponse } from "next/server";
import { executeReActAgent } from "@/lib/agent/react-engine";

export interface AssistantMetricCard {
  title: string;
  value: string;
  badge?: string;
  variant?: "default" | "accent" | "warning" | "success";
}

export interface AssistantChartPoint {
  label: string;
  valor: number;
}

export interface AssistantResponse {
  answer: string;
  metrics?: AssistantMetricCard[];
  chartData?: AssistantChartPoint[];
  chartType?: "bar" | "donut" | "metric";
  sqlQuery?: string;
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

    // Execução 100% Agêntica via Motor ReAct + Memória Conversacional + DuckDB
    const reactResult = await executeReActAgent({
      message,
      history,
      portalSlug,
      year,
      currentRoute,
      traceId,
    });

    return NextResponse.json({
      answer: reactResult.answer,
      metrics: reactResult.metrics,
      chartType: reactResult.chartType || "metric",
      sqlQuery: reactResult.sqlQuery,
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
