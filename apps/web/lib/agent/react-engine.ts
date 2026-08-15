import { google } from "@ai-sdk/google";
import { generateObject, generateText, jsonSchema, tool } from "ai";
import { queryDuckDbParquet } from "../duckdb-executor";
import { FISCAL_TAXONOMY, trackMcpToolCall } from "../mcp/transparencia-mcp";
import { buildLayeredContext } from "../skills/context-builder";

export interface ReActExecuteOptions {
  message: string;
  portalSlug?: string;
  year?: number;
  currentRoute?: string;
  traceId?: string;
  maxSteps?: number;
}

export interface ReActResult {
  answer: string;
  metrics?: Array<{
    title: string;
    value: string;
    variant?: "default" | "accent" | "warning" | "success";
  }>;
  chartData?: Array<{ label: string; valor: number }>;
  chartType?: "bar" | "donut" | "metric";
  sqlQuery?: string;
  stepsCount: number;
  autoCorrected: boolean;
}

const finalAnswerSchema = jsonSchema<{
  answer: string;
  metrics?: {
    title: string;
    value: string;
    variant?: "default" | "accent" | "warning" | "success";
  }[];
  chartType?: "bar" | "donut" | "metric";
}>({
  type: "object",
  properties: {
    answer: {
      type: "string",
      description:
        "Resposta amigável em linguagem simples para o cidadão sem mencionar termos de banco de dados",
    },
    metrics: {
      type: "array",
      items: {
        type: "object",
        properties: {
          title: { type: "string" },
          value: { type: "string" },
          variant: {
            type: "string",
            enum: ["default", "accent", "warning", "success"],
          },
        },
        required: ["title", "value"],
      },
    },
    chartType: { type: "string", enum: ["bar", "donut", "metric"] },
  },
  required: ["answer"],
});

export async function executeReActAgent(
  options: ReActExecuteOptions,
): Promise<ReActResult> {
  const startTime = Date.now();
  const portalSlug = options.portalSlug || "porciuncula_prefeitura";
  const year = options.year || 2025;
  const currentRoute = options.currentRoute || "/visao-geral";

  const systemContext = buildLayeredContext({
    portalSlug,
    year,
    currentRoute,
  });

  let executedSql = "";
  let queryResults: Record<string, unknown>[] = [];
  let autoCorrected = false;

  const apiKey =
    process.env.GOOGLE_GENERATIVE_AI_API_KEY || process.env.GEMINI_API_KEY;

  if (!apiKey) {
    throw new Error("API Key de IA não configurada.");
  }

  // Definição das Ferramentas MCP para o Motor ReAct
  const tools = {
    listMartsTaxonomia: tool({
      description: "Lista a taxonomia dos marts Parquet e domínios disponíveis",
      parameters: jsonSchema<{ domain?: string }>({
        type: "object",
        properties: { domain: { type: "string" } },
      }),
      execute: async ({ domain }) => {
        const allMarts = FISCAL_TAXONOMY.flatMap((group) =>
          group.marts.map((m) => ({
            domain: group.domain,
            tableName: m.table,
            description: m.description,
          })),
        );

        if (domain) {
          return allMarts.filter((m) =>
            m.domain.toLowerCase().includes(domain.toLowerCase()),
          );
        }
        return allMarts;
      },
    }),

    getMartSchema: tool({
      description:
        "Obtém o schema detalhado (colunas e tipos de dados) de uma tabela",
      parameters: jsonSchema<{ tableName: string }>({
        type: "object",
        properties: { tableName: { type: "string" } },
        required: ["tableName"],
      }),
      execute: async ({ tableName }) => {
        for (const group of FISCAL_TAXONOMY) {
          const found = group.marts.find((m) => m.table === tableName);
          if (found) {
            return { tableName: found.table, columns: found.columns };
          }
        }
        return { error: `Tabela '${tableName}' não encontrada.` };
      },
    }),

    queryDuckDbMart: tool({
      description:
        "Executa uma consulta SQL no DuckDB. Sempre inclua CAST(SUM(...) AS DOUBLE) e filtre por portal_slug e ano",
      parameters: jsonSchema<{ sql: string }>({
        type: "object",
        properties: { sql: { type: "string" } },
        required: ["sql"],
      }),
      execute: async ({ sql }) => {
        executedSql = sql;
        try {
          const rows = await queryDuckDbParquet(sql);
          queryResults = rows;

          if (rows.length === 0) {
            autoCorrected = true;
            return {
              warning:
                "A consulta retornou 0 resultados. Verifique se o nome de fornecedor/filtro necessita de ILIKE '%termo%' ou se o portal_slug e ano estão corretos.",
              rows: [],
            };
          }
          return { rowCount: rows.length, data: rows.slice(0, 10) };
        } catch (err) {
          autoCorrected = true;
          const errMsg = err instanceof Error ? err.message : String(err);
          return {
            error: `Erro SQL DuckDB: ${errMsg}. Por favor, ajuste a query SQL usando colunas válidas.`,
          };
        }
      },
    }),
  };

  // Loop ReAct via Vercel AI SDK generateText
  const response = await generateText({
    model: google("gemini-1.5-flash"),
    system: `${systemContext}\n\nInstruções ReAct:\n1. Pense passo a passo antes de agir.\n2. Inspecione a taxonomia/schema se houver dúvida sobre colunas.\n3. Execute a query SQL DuckDB usando a ferramenta queryDuckDbMart.\n4. Se a query falhar ou retornar 0 linhas, ajuste a query e tente novamente (Auto-Correção).`,
    prompt: `PERGUNTA DO CIDADÃO: "${options.message}"`,
    tools,
    maxSteps: options.maxSteps || 4,
  });

  // Geração final do objeto estruturado com base nos resultados obtidos
  const { object } = await generateObject({
    model: google("gemini-1.5-flash"),
    schema: finalAnswerSchema,
    prompt: `Com base no seguinte diálogo ReAct e resultados da consulta SQL:\n\n${response.text}\n\nResultados obtidos: ${JSON.stringify(queryResults.slice(0, 5))}\n\nFormate a resposta final clara para o cidadão.`,
  });

  const result: ReActResult = {
    answer: object.answer,
    metrics: object.metrics,
    chartType: object.chartType || "metric",
    sqlQuery: executedSql,
    stepsCount: response.steps.length,
    autoCorrected,
    chartData: queryResults.slice(0, 5).map((row) => ({
      label: String(
        row.contrato_numero ||
          row.fornecedor_nome ||
          row.label ||
          row.objeto ||
          "Item",
      ),
      valor: Number(
        row.pago ||
          row.valor ||
          row.total_pago ||
          row.valor_contrato ||
          row.total_arrecadado ||
          0,
      ),
    })),
  };

  // Telemetria PostHog ($ai_generation)
  await trackMcpToolCall(
    "react_agent_execution",
    {
      input: { message: options.message, portalSlug, year },
      output: result,
      latencyMs: Date.now() - startTime,
    },
    { traceId: options.traceId, model: "gemini-1.5-flash" },
  );

  return result;
}
