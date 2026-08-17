import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { generateObject, jsonSchema } from "ai";
import { queryDuckDbParquet } from "../duckdb-executor";
import { logger } from "../logger";
import { FISCAL_TAXONOMY, trackMcpToolCall } from "../mcp/transparencia-mcp";
import { buildLayeredContext } from "../skills/context-builder";

export interface ReActExecuteOptions {
  message: string;
  history?: Array<{ role: "user" | "assistant"; content: string }>;
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

const sqlGenerationSchema = jsonSchema<{
  sqlQuery: string;
  reasoning?: string;
}>({
  type: "object",
  properties: {
    sqlQuery: {
      type: "string",
      description:
        "Query SQL DuckDB válida filtrada estritamente por portal_slug e ano",
    },
    reasoning: {
      type: "string",
      description: "Justificativa da escolha da tabela e colunas",
    },
  },
  required: ["sqlQuery"],
});

const finalAnswerSchema = jsonSchema<{
  answer: string;
  metrics?: Array<{
    title: string;
    value: string;
    variant?: "default" | "accent" | "warning" | "success";
  }>;
  chartData?: Array<{ label: string; valor: number }>;
  chartType?: "bar" | "donut" | "metric";
}>({
  type: "object",
  properties: {
    answer: {
      type: "string",
      description: "Resposta explicativa e direta para o cidadão",
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
    chartData: {
      type: "array",
      items: {
        type: "object",
        properties: {
          label: { type: "string" },
          valor: { type: "number" },
        },
        required: ["label", "valor"],
      },
    },
    chartType: {
      type: "string",
      enum: ["bar", "donut", "metric"],
    },
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

  const apiKey =
    process.env.GOOGLE_GENERATIVE_AI_API_KEY ||
    process.env.GEMINI_API_KEY ||
    process.env.NEXT_PUBLIC_GEMINI_API_KEY;

  if (!apiKey) {
    return {
      answer:
        "⚠️ **Chave de API de IA Não Configurada**\n\nPara habilitar as consultas inteligentes com o motor agêntico, adicione a variável `GOOGLE_GENERATIVE_AI_API_KEY` ou `GEMINI_API_KEY` com sua chave do Google Gemini no arquivo `.env.local` da aplicação web (`apps/web/.env.local`).",
      metrics: [
        { title: "Status IA", value: "Aguardando API Key", variant: "warning" },
      ],
      stepsCount: 0,
      autoCorrected: false,
    };
  }

  const google = createGoogleGenerativeAI({ apiKey });
  const candidateModels = Array.from(
    new Set(
      [
        process.env.GEMINI_MODEL,
        "gemini-3.1-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3.6-flash",
      ].filter(Boolean) as string[],
    ),
  );

  async function generateWithFallback<T>(params: {
    // biome-ignore lint/suspicious/noExplicitAny: generic AI SDK schema typing
    schema: any;
    prompt: string;
    system?: string;
  }): Promise<{ object: T }> {
    let lastError: Error | null = null;
    for (const modelName of candidateModels) {
      try {
        const result = await generateObject({
          model: google(modelName),
          schema: params.schema,
          system: params.system,
          prompt: params.prompt,
          maxTokens: 4096,
        });
        return result as { object: T };
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        const errMsg = lastError.message;
        if (
          errMsg.includes("Quota exceeded") ||
          errMsg.includes("rate-limit") ||
          errMsg.includes("limit: 20") ||
          errMsg.includes("404") ||
          errMsg.includes("not found") ||
          errMsg.includes("Unexpected end of JSON") ||
          errMsg.includes("JSON") ||
          errMsg.includes("SyntaxError")
        ) {
          continue;
        }
        throw lastError;
      }
    }
    throw lastError || new Error("Nenhum modelo de IA disponível.");
  }

  let historyContext = "";
  if (options.history && options.history.length > 0) {
    const turnsText = options.history
      .slice(-4)
      .map(
        (h) =>
          `${h.role === "user" ? "Cidadão" : "Assistente"}: "${h.content.replace(/\n+/g, " ").slice(0, 300)}"`,
      )
      .join("\n");
    historyContext = `\n\nHISTÓRICO RECENTE DAS PERGUNTAS E RESPOSTAS ANTERIORES:\n${turnsText}\n\nNOTA DE MEMÓRIA CONVERSACIONAL: Se a pergunta atual contiver pronomes como "disso", "dele", "dela", "nesse período" ou pedir desdobramento da resposta anterior, reutilize os filtros de anos, fornecedores, órgãos ou categorias citados no histórico acima.`;
  }

  let executedSql = "";
  let queryResults: Record<string, unknown>[] = [];
  let autoCorrected = false;
  let stepsCount = 2;

  logger.debug(
    `Nova pergunta do Cidadão: "${options.message}" (Portal: ${portalSlug}, Exercício: ${year})`,
  );

  try {
    // PASSO 1: Geração Agêntica da Query SQL com base no Contexto, Memória Multi-Turno e Taxonomia
    const step1 = await generateWithFallback<{
      sqlQuery: string;
      reasoning?: string;
    }>({
      schema: sqlGenerationSchema,
      system: `${systemContext}\n\nREGRAS MANDATÓRIAS SQL DUCKDB:\n1. Escreva queries válidas para DuckDB.\n2. Toda agregação (SUM, AVG) DEVE ser convertida com CAST(SUM(...) AS DOUBLE).\n3. Sempre filtre por portal_slug = '${portalSlug}'. Se o cidadão citar um ano específico na pergunta ou no histórico recente (ex: 2023, 2024, 2026), utilize o(s) ano(s) solicitados. Caso contrário, se nenhum ano for citado, utilize ano = ${year}.\n4. CONSULTAS MULTI-TABELAS & CTEs: Você pode e deve fazer JOINs ou usar CTEs (WITH) cruzando tabelas de fatos (fct_*) e dimensões (dim_*) quando a pergunta exigir identificar termos ou códigos específicos (ex: para 'merenda escolar', busque elementos/naturezas de alimentação ou JOIN com dim_elemento_despesa / dim_natureza_despesa; para fornecedores de um setor, faça JOIN com dim_credor).\n5. LÓGICA BOOLEANA & UNACCENT MANDATÓRIO: Para buscar itens específicos (ex: merenda escolar, medicamentos, combustíveis), NUNCA conecte o termo específico com a função genérica usando OR (ex: JAMAIS use 'OR funcao_nome LIKE %Educação%'). Em TODOS os filtros textuais (historico, objeto, descricao, fornecedor_nome), utilize OBRIGATORIAMENTE unaccent(lower(coluna)) LIKE '%termo_sem_acento%' (ex: use '%alimentacao%', jamais '%alimentação%').\n6. Use apenas tabelas e colunas declaradas na taxonomia oficial.`,
      prompt: `TAXONOMIA DE MARTS DISPONÍVEIS:\n${JSON.stringify(FISCAL_TAXONOMY, null, 2)}${historyContext}\n\nPERGUNTA ATUAL DO CIDADÃO: "${options.message}"`,
    });

    executedSql = step1.object.sqlQuery;

    logger.debug(`Query SQL Gerada (Passo 1): ${executedSql}`);

    // PASSO 2: Execução no DuckDB WASM Parquet com Auto-Correção Agêntica
    try {
      queryResults = await queryDuckDbParquet(executedSql);
      logger.debug(`DuckDB Retornou: ${queryResults.length} linha(s)`);

      // Auto-Correção se retornar 0 linhas
      if (queryResults.length === 0) {
        autoCorrected = true;
        stepsCount++;
        logger.debug(
          "0 resultados obtidos. Disparando Auto-Correção Agêntica...",
        );
        const stepCorrected = await generateWithFallback<{
          sqlQuery: string;
          reasoning?: string;
        }>({
          schema: sqlGenerationSchema,
          system: systemContext,
          prompt: `A query anterior '${executedSql}' retornou 0 resultados.\nAjuste a query para o cidadão. Dica: use filtros ILIKE '%termo%' se for nome de fornecedor/descrição.\n\nTAXONOMIA:\n${JSON.stringify(FISCAL_TAXONOMY, null, 2)}${historyContext}\n\nPERGUNTA: "${options.message}"`,
        });
        executedSql = stepCorrected.object.sqlQuery;
        logger.debug(`Query Corrigida: ${executedSql}`);
        queryResults = await queryDuckDbParquet(executedSql);
      }
    } catch (sqlErr) {
      autoCorrected = true;
      stepsCount++;
      const errMsg = sqlErr instanceof Error ? sqlErr.message : String(sqlErr);
      logger.debug(
        `Falha DuckDB: ${errMsg}. Disparando Auto-Correção Agêntica...`,
      );
      const stepCorrected = await generateWithFallback<{
        sqlQuery: string;
        reasoning?: string;
      }>({
        schema: sqlGenerationSchema,
        system: systemContext,
        prompt: `A query anterior '${executedSql}' falhou com o erro: '${errMsg}'.\nCorrija a sintaxe e use apenas colunas válidas da taxonomia.\n\nTAXONOMIA:\n${JSON.stringify(FISCAL_TAXONOMY, null, 2)}${historyContext}\n\nPERGUNTA: "${options.message}"`,
      });
      executedSql = stepCorrected.object.sqlQuery;
      logger.debug(`Query Corrigida: ${executedSql}`);
      queryResults = await queryDuckDbParquet(executedSql);
    }

    // PASSO 3: Síntese Agêntica Final para o Cidadão (Resposta + Métricas + Gráfico)
    const stepFinal = await generateWithFallback<{
      answer: string;
      metrics?: Array<{
        title: string;
        value: string;
        variant?: "default" | "accent" | "warning" | "success";
      }>;
      chartData?: Array<{ label: string; valor: number }>;
      chartType?: "bar" | "donut" | "metric";
    }>({
      schema: finalAnswerSchema,
      system: systemContext,
      prompt: `Com base nos dados orçamentários extraídos do DuckDB:\nQuery executada: ${executedSql}\nResultados obtidos: ${JSON.stringify(queryResults.slice(0, 8))}${historyContext}\n\nPERGUNTA DO CIDADÃO: "${options.message}"\n\nFormate uma resposta explicativa clara, perfeitamente articulada com o histórico da conversa. Limite 'metrics' a no máximo 4 itens e 'chartData' a no máximo 5 itens para manter a resposta concisa.`,
    });

    const durationMs = Date.now() - startTime;
    logger.debug(
      `Resposta final concluída em ${durationMs}ms (${stepsCount} passos).`,
    );

    await trackMcpToolCall(
      "react_agent_execution",
      {
        input: { message: options.message, portalSlug, year },
        output: {
          answer: stepFinal.object.answer,
          sqlQuery: executedSql,
          stepsCount,
        },
        latencyMs: durationMs,
      },
      { traceId: options.traceId },
    );

    return {
      answer: stepFinal.object.answer,
      metrics: stepFinal.object.metrics,
      chartData: stepFinal.object.chartData,
      chartType: stepFinal.object.chartType,
      sqlQuery: executedSql,
      stepsCount,
      autoCorrected,
    };
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err);
    if (
      errMsg.includes("Quota exceeded") ||
      errMsg.includes("rate-limit") ||
      errMsg.includes("limit: 20")
    ) {
      return {
        answer:
          "⏳ **Limite de Requisições Atingido na Cota Gratuita do Gemini**\n\nA chave de API gratuita do Google Gemini atingiu o limite de requisições por minuto. Por favor, aguarde alguns segundos e tente novamente.",
        metrics: [
          {
            title: "Cota Gratuita",
            value: "20 RPM Excedido",
            variant: "warning",
          },
        ],
        stepsCount: 0,
        autoCorrected: false,
      };
    }
    throw err;
  }
}
