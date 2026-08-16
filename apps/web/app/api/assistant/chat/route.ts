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

    // Execução 100% Agêntica via Motor ReAct + Ferramentas MCP + Auto-Correção
    const reactResult = await executeReActAgent({
      message,
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
    // biome-ignore lint/suspicious/noConsole: error logger for diagnostics
    console.error("API Assistant Chat Agent Error:", error);
    return NextResponse.json(
      {
        error:
          "Não foi possível processar a consulta agêntica no momento. Verifique se a chave de API de IA está configurada.",
      },
      { status: 500 },
    );
  }
}
