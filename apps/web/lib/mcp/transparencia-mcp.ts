import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { getPostHogServer } from "../../posthog-server";
import { queryDuckDbParquet } from "../duckdb-executor";

// Catálogo de Taxonomia dos 25 Marts Parquet de Transparência Fiscal
export const FISCAL_TAXONOMY = [
  {
    domain: "Posição Fiscal",
    marts: [
      {
        table: "fct_posicao_fiscal_metricas",
        description:
          "Saldos agregados de arrecadação, despesas pagas e restos a pagar por ano e portal_slug.",
        columns: [
          "portal_slug",
          "ano",
          "total_arrecadado",
          "despesas_pagas",
          "restos_pagos_no_ano",
          "restos_pendentes_adm_anterior",
          "restos_pendentes_adm_atual",
          "saldo_estimado",
        ],
      },
      {
        table: "fct_posicao_fiscal_detalhes_metricas",
        description:
          "Detalhamento diário da posição de caixa, receitas e despesas acumuladas.",
        columns: [
          "portal_slug",
          "ano",
          "data",
          "total_arrecadado",
          "total_pago",
          "saldo_diario",
        ],
      },
    ],
  },
  {
    domain: "Despesas e Credores",
    marts: [
      {
        table: "fct_analise_despesas_metricas",
        description:
          "Agregação de empenhado, liquidado e pago agrupados por órgão, unidade e função contábil.",
        columns: [
          "portal_slug",
          "ano",
          "orgao_codigo",
          "unidade_codigo",
          "funcao_codigo",
          "total_empenhado",
          "total_liquidado",
          "total_pago",
        ],
      },
      {
        table: "fct_despesas",
        description: "Listagem individual detalhada de empenhos e pagamentos.",
        columns: [
          "portal_slug",
          "ano",
          "numero_empenho",
          "credor_nome",
          "credor_cpf_cnpj",
          "valor_empenhado",
          "valor_liquidado",
          "valor_pago",
          "elemento_codigo",
          "historico",
        ],
      },
      {
        table: "fct_despesas_fornecedores_metricas",
        description:
          "Top fornecedores e fornecedores dominantes com cálculo HHI.",
        columns: [
          "portal_slug",
          "ano",
          "credor_nome",
          "credor_cpf_cnpj",
          "total_pago",
          "participacao_pct",
        ],
      },
    ],
  },
  {
    domain: "Receitas e Emendas",
    marts: [
      {
        table: "fct_fontes_receita_metricas",
        description:
          "Arrecadação de receitas orçamentárias, extra-orçamentárias e emendas PIX.",
        columns: [
          "portal_slug",
          "ano",
          "total_previsto",
          "total_arrecadado",
          "emendas_pix_arrecadado",
          "receita_extra_orcamentaria_arrecadado",
        ],
      },
      {
        table: "fct_emendas",
        description:
          "Emendas parlamentares individuais e PIX recebidas pelo município.",
        columns: [
          "portal_slug",
          "ano",
          "autor_nome",
          "tipo_emenda",
          "valor_arrecadado",
          "destinacao",
        ],
      },
    ],
  },
  {
    domain: "Saúde e CAPREM",
    marts: [
      {
        table: "fct_historia_saude_metricas",
        description:
          "Métricas de aplicação em Saúde, convênios e emendas de saúde.",
        columns: [
          "portal_slug",
          "ano",
          "total_liquidado",
          "total_pago",
          "percentual_aplicacao_saude",
        ],
      },
      {
        table: "fct_historia_caprem_metricas",
        description:
          "Métricas atuariais da previdência municipal (CAPREM), retenções e aportes.",
        columns: [
          "portal_slug",
          "ano",
          "total_empenhado_patronal",
          "total_pago_patronal",
          "saldo_atuarial",
        ],
      },
    ],
  },
  {
    domain: "Licitações e Contratos",
    marts: [
      {
        table: "fct_licitacoes_gaps_metricas",
        description:
          "Métricas de dispensas de licitação e contratações diretas com validação de limites fiscais.",
        columns: [
          "portal_slug",
          "ano",
          "valor_contrato",
          "isento_legalmente",
          "objeto",
          "fornecedor_nome",
        ],
      },
      {
        table: "fct_contratos_servicos_vigentes",
        description:
          "Contratos vigentes de prestação de serviços com status de execução orçamentária.",
        columns: [
          "portal_slug",
          "ano",
          "numero_contrato",
          "contratado_nome",
          "valor_total",
          "total_liquidado",
          "total_pago",
          "status_execucao",
        ],
      },
    ],
  },
  {
    domain: "Pessoal e Folha",
    marts: [
      {
        table: "fct_pessoal_folha_metricas",
        description:
          "Totais de folha bruta, líquidos, proventos e 13º salário.",
        columns: [
          "portal_slug",
          "ano",
          "total_folha_bruta",
          "total_pago_pessoal",
          "quantidade_servidores",
        ],
      },
    ],
  },
];

export interface TraceOptions {
  traceId?: string;
  model?: string;
  distinctId?: string;
}

export interface ToolPayload {
  input: Record<string, unknown>;
  output: unknown;
  latencyMs: number;
}

// Rastreamento de Observabilidade via PostHog ($ai_generation)
export async function trackMcpToolCall(
  toolName: string,
  payload: ToolPayload,
  options: TraceOptions = {},
): Promise<void> {
  const posthog = getPostHogServer();
  if (!posthog) return;

  const distinctId = options.distinctId || "agent-mcp-user";
  const traceId =
    options.traceId ||
    `trace-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

  posthog.capture({
    distinctId,
    event: "$ai_generation",
    properties: {
      $ai_trace_id: traceId,
      $ai_model: options.model || "gemini-3.6-flash",
      $ai_provider: "google",
      $ai_input: JSON.stringify(payload.input),
      $ai_output: JSON.stringify(payload.output),
      $ai_latency: payload.latencyMs / 1000,
      $ai_http_status: 200,
      $ai_tool_name: toolName,
      $ai_is_mcp: true,
      domain: "transparencia_fiscal",
    },
  });

  await posthog.flush();
}

export function createTransparenciaMcpServer(): Server {
  const server = new Server(
    {
      name: "transparencia-mcp",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    },
  );

  // 1. Definição das Ferramentas MCP
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "list_marts_taxonomia",
          description:
            "Lista a taxonomia completa dos 25 marts Parquet de transparência fiscal divididos por domínio.",
          inputSchema: {
            type: "object",
            properties: {
              domain: {
                type: "string",
                description:
                  "Filtro opcional por domínio (ex: 'Posição Fiscal', 'Despesas e Credores', 'Saúde e CAPREM')",
              },
            },
          },
        },
        {
          name: "get_mart_schema",
          description:
            "Retorna a estrutura de colunas e descrição detalhada de um mart Parquet específico.",
          inputSchema: {
            type: "object",
            properties: {
              table_name: {
                type: "string",
                description:
                  "Nome da tabela mart (ex: 'fct_posicao_fiscal_metricas')",
              },
            },
            required: ["table_name"],
          },
        },
        {
          name: "query_duckdb_mart",
          description:
            "Executa uma consulta SQL analítica (SELECT) via DuckDB contra os arquivos Parquet de métricas.",
          inputSchema: {
            type: "object",
            properties: {
              sql_query: {
                type: "string",
                description:
                  "Query SQL SELECT para DuckDB (ex: SELECT CAST(SUM(total_arrecadado) AS DOUBLE) as total FROM fct_posicao_fiscal_metricas WHERE portal_slug = 'porciuncula' AND ano = 2025)",
              },
              trace_id: {
                type: "string",
                description: "ID opcional de rastreamento de observabilidade",
              },
            },
            required: ["sql_query"],
          },
        },
      ],
    };
  });

  // 2. Execução das Ferramentas MCP com Tracing do PostHog
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    const startTime = Date.now();

    if (name === "list_marts_taxonomia") {
      const domainFilter = (args?.domain as string | undefined)?.toLowerCase();
      const result = domainFilter
        ? FISCAL_TAXONOMY.filter((t) =>
            t.domain.toLowerCase().includes(domainFilter),
          )
        : FISCAL_TAXONOMY;

      await trackMcpToolCall(name, {
        input: args || {},
        output: result,
        latencyMs: Date.now() - startTime,
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    }

    if (name === "get_mart_schema") {
      const tableName = args?.table_name as string;
      let matchedMart = null;

      for (const dom of FISCAL_TAXONOMY) {
        const found = dom.marts.find((m) => m.table === tableName);
        if (found) {
          matchedMart = found;
          break;
        }
      }

      const result = matchedMart || {
        error: `Tabela '${tableName}' não encontrada na taxonomia.`,
      };
      await trackMcpToolCall(name, {
        input: args || {},
        output: result,
        latencyMs: Date.now() - startTime,
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    }

    if (name === "query_duckdb_mart") {
      const sqlQuery = args?.sql_query as string;
      const traceId = args?.trace_id as string | undefined;

      if (!/^\s*(SELECT|WITH)\b/i.test(sqlQuery)) {
        const errorResult = {
          error: "Apenas consultas de leitura SELECT/WITH são permitidas.",
        };
        await trackMcpToolCall(
          name,
          {
            input: args || {},
            output: errorResult,
            latencyMs: Date.now() - startTime,
          },
          { traceId },
        );
        return {
          isError: true,
          content: [{ type: "text", text: JSON.stringify(errorResult) }],
        };
      }

      try {
        const rows = await queryDuckDbParquet(sqlQuery);
        const outputPayload = {
          row_count: rows.length,
          sample: rows.slice(0, 3),
        };
        await trackMcpToolCall(
          name,
          {
            input: args || {},
            output: outputPayload,
            latencyMs: Date.now() - startTime,
          },
          { traceId },
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { row_count: rows.length, data: rows },
                null,
                2,
              ),
            },
          ],
        };
      } catch (err) {
        const errorMsg = {
          error: err instanceof Error ? err.message : String(err),
        };
        await trackMcpToolCall(
          name,
          {
            input: args || {},
            output: errorMsg,
            latencyMs: Date.now() - startTime,
          },
          { traceId },
        );
        return {
          isError: true,
          content: [{ type: "text", text: JSON.stringify(errorMsg) }],
        };
      }
    }

    throw new Error(`Ferramenta MCP '${name}' não encontrada.`);
  });

  return server;
}
