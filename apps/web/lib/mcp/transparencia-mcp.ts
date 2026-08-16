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
          "Mart de métricas agregadas de posição fiscal diária e anual por portal, entidade e exercício",
        columns: [
          "posicao_fiscal_id",
          "portal_slug",
          "empresa_id",
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
          "Mart de detalhes de restos a pagar e credores por portal, entidade e exercício",
        columns: [
          "posicao_fiscal_detalhes_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "administracao",
          "valor_pendente",
          "fornecedor_nome",
        ],
      },
      {
        table: "fct_despesas_restos_metricas",
        description:
          "Mart de métricas consolidadas de restos a pagar e passivos financeiros.",
        columns: [
          "restos_metricas_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "restos_inscritos",
          "restos_pagos",
          "restos_cancelados",
          "saldo_restos",
          "divida_mais_antiga_ano",
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
          "Mart de métricas agregadas de análise de despesas por portal, entidade, exercício, órgão, unidade e função",
        columns: [
          "analise_despesas_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "orgao_codigo",
          "unidade_codigo",
          "funcao_codigo",
          "total_dotacao_atualizada",
          "total_empenhado",
          "total_liquidado",
          "total_pago",
        ],
      },
      {
        table: "fct_despesas_fornecedores_metricas",
        description:
          "Mart de métricas de fornecedores agregadas por portal, entidade, exercício e fornecedor",
        columns: [
          "fornecedores_metricas_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "fornecedor_codigo",
          "fornecedor_nome",
          "fornecedor_cidade_clean",
          "total_empenhado",
          "total_pago",
        ],
      },
      {
        table: "fct_despesas_diarias_metricas",
        description:
          "Mart de métricas de diárias agregadas por portal, entidade, exercício, favorecido e cargo",
        columns: [
          "diarias_metricas_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "favorecido",
          "cargo",
          "total_valor",
          "qtd_concessoes",
        ],
      },
      {
        table: "fct_despesas_por_orgao",
        description:
          "Despesas agregadas por órgão/secretaria, lidas da tabela raw do portal e com cast numérico nos valores financeiros",
        columns: [
          "empresa",
          "ano",
          "codigo",
          "descricao",
          "empenhado",
          "liquidado",
          "pago",
          "dotacao_atualizada",
        ],
      },
      {
        table: "fct_despesas_por_unidade",
        description:
          "Despesas agregadas por unidade orçamentária, lidas da tabela raw do portal e com cast numérico nos valores financeiros",
        columns: [
          "portal_slug",
          "empresa",
          "ano",
          "codigo",
          "descricao",
          "empenhado",
          "liquidado",
          "pago",
          "dotacao_atualizada",
        ],
      },
      {
        table: "fct_despesas_por_fornecedor",
        description:
          "Despesas agregadas por fornecedor, lidas da tabela raw do portal e com cast numérico nos valores financeiros",
        columns: [
          "empresa",
          "ano",
          "codigo",
          "descricao",
          "fornecedor_cpf_cnpj",
          "fornecedor_cidade",
          "fornecedor_cidade_clean",
          "empenhado",
          "liquidado",
          "pago",
        ],
      },
      {
        table: "fct_despesas",
        description:
          "Fato de despesas consolidadas com empenho líquido calculado (exclui anulações do fluxo principal)",
        columns: [
          "despesa_id",
          "portal_slug",
          "fonte",
          "ano",
          "empresa_id",
          "empenho_id",
          "pk_empenho",
          "tipo_empenho",
          "orgao_codigo",
          "unidade_codigo",
          "funcao",
          "funcao_nome",
          "subfuncao",
          "subfuncao_nome",
          "elemento",
          "natureza_despesa",
          "grupo_natureza",
          "modalidade",
          "programa",
          "programa_nome",
          "proj_atividade",
          "projeto_atividade_nome",
          "mes",
          "fornecedor_nome",
          "fornecedor_cpf_cnpj",
          "licitacao_numero",
          "licitacao_modalidade",
          "fonte_recurso_desc",
          "descricao",
          "credor_id",
          "orgao_id",
          "data_empenho",
          "empenhado",
          "empenhado_liquido",
          "liquidado",
          "pago",
          "dotacao_inicial",
          "alteracao_dotacao",
          "dotacao_atualizada",
          "reforco",
          "valor_anulacoes",
        ],
      },
      {
        table: "dim_credor",
        description: "Credores/fornecedores únicos por portal",
        columns: [
          "credor_id",
          "portal_slug",
          "fornecedor_cpf_cnpj",
          "fornecedor_nome",
          "fornecedor_cidade",
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
          "Mart de métricas agregadas de fontes de receita e transferências por portal e ano",
        columns: [
          "fontes_receita_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "receita_propria_previsto",
          "receita_propria_arrecadado",
          "transferencias_uniao_previsto",
          "transferencias_uniao_arrecadado",
          "transferencias_estado_previsto",
          "transferencias_estado_arrecadado",
          "receita_extra_orcamentaria_arrecadado",
          "total_previsto",
          "total_arrecadado",
          "pct_propria",
          "alerta_dependencia",
          "fpm_arrecadado",
          "icms_arrecadado",
          "iss_iptu_arrecadado",
          "emendas_pix_arrecadado",
          "emendas_individuais_arrecadado",
          "emendas_total_arrecadado",
          "emendas_total_empenhado",
        ],
      },
      {
        table: "fct_receita_extra_orcamentaria",
        description:
          "Mart analítico com o somatório total de receitas extra-orçamentárias por portal, empresa e ano",
        columns: [
          "receita_extra_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "codigo",
          "descricao",
          "valor_arrecadado",
        ],
      },
      {
        table: "fct_receitas",
        description:
          "Fato de receitas consolidadas (orçamentária, união e estado) de todos os portais",
        columns: [
          "receita_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "tipo_receita",
          "codigo",
          "descricao",
          "previsao_atualizada",
          "arrecadado",
        ],
      },
      {
        table: "fct_emendas",
        description:
          "Fato de emendas parlamentares consolidadas de todos os portais",
        columns: [
          "emenda_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "numero_emenda",
          "resumo",
          "valor_total",
          "empenhado",
          "autor",
          "tipo_emenda",
          "esfera_origem",
          "ato_normativo",
          "destinacao",
        ],
      },
      {
        table: "fct_transferencias",
        description: "Fato de transferências consolidadas de todos os portais",
        columns: [
          "transferencia_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "mes",
          "entidade_pagadora",
          "entidade_recebedora",
          "repasse",
          "devolucao",
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
          "Mart de métricas agregadas de execução orçamentária, financeira e fontes de receita da Saúde por portal e ano",
        columns: [
          "historia_saude_id",
          "portal_slug",
          "ano",
          "dotacao_total",
          "total_empenhado",
          "total_liquidado",
          "total_pago",
          "medicamentos_insumos_empenhado",
          "medicamentos_insumos_pago",
          "judicializacao_empenhado",
          "judicializacao_pago",
          "emendas_saude_arrecadado",
          "hhi_concentracao_fornecedores",
          "receita_uniao_saude",
          "receita_estado_saude",
          "repasses_prefeitura_saude",
          "uniao_sus_pct",
          "estado_pct",
          "propria_pct",
        ],
      },
      {
        table: "fct_historia_caprem_metricas",
        description:
          "Mart de métricas agregadas atuariais do RPPS e CAPREM por portal e ano",
        columns: [
          "historia_caprem_id",
          "portal_slug",
          "ano",
          "total_aporte_exigido",
          "total_aporte_quitado",
          "taxa_adimplencia_aporte",
          "total_empenhado_patronal",
          "total_liquidado_patronal",
          "total_pago_patronal",
          "rombo_patronal_nao_repassado",
          "total_amortizacao_divida",
          "total_casp_plano_saude",
          "total_empenhado",
          "total_liquidado",
          "total_pago",
          "servidores_efetivos",
          "servidores_temporarios",
        ],
      },
      {
        table: "fct_caprem_tendencia_atuarial_metricas",
        description:
          "Mart de série histórica atuarial e amortização de dívida previdenciária (Elementos 97 e 71)",
        columns: [
          "caprem_tendencia_id",
          "portal_slug",
          "ano",
          "aporte_exigido",
          "aporte_quitado",
          "taxa_adimplencia",
          "amortizacao_divida",
        ],
      },
      {
        table: "fct_caprem_entidades_metricas",
        description:
          "Mart de repasses e contribuições ao CAPREM por entidade municipal",
        columns: [
          "caprem_entidade_id",
          "portal_slug",
          "ano",
          "entidade",
          "empenhado",
          "liquidado",
          "pago",
          "taxa_execucao",
        ],
      },
      {
        table: "fct_caprem_natureza_metricas",
        description:
          "Mart de repasses e despesas do CAPREM agrupados por elemento, natureza e destino contábil",
        columns: [
          "caprem_natureza_id",
          "portal_slug",
          "ano",
          "empenho_id",
          "elemento",
          "natureza_despesa",
          "destino",
          "descricao",
          "data_empenho",
          "empenhado",
          "liquidado",
          "pago",
        ],
      },
      {
        table: "fct_caprem_cadprev_metricas",
        description:
          "Mart de acordos de confissão e parcelamento de dívida previdenciária junto ao CAPREM (Elemento 71), filtrados para excluir outras despesas de amortização não relacionadas (ex: multas de INSS/RGPS à Receita Federal que também usam o Elemento 71)",
        columns: [
          "caprem_cadprev_id",
          "portal_slug",
          "ano",
          "empenho_id",
          "descricao",
          "data_empenho",
          "empenhado",
          "pago",
        ],
      },
    ],
  },
  {
    domain: "Licitações e Contratos",
    marts: [
      {
        table: "fct_licitacoes_metricas",
        description:
          "Mart de métricas consolidadas de contratações (licitações próprias, adesão a atas internas, adesões a atas externas e gaps sem licitação).",
        columns: [
          "licitacao_metricas_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "tipo_contratacao",
          "numero",
          "licitacao_numero",
          "contrato_numero",
          "fornecedor_nome",
          "objeto",
          "modalidade",
          "fundlegal",
          "carona",
          "mes",
          "numero_obra",
          "tipo_obra",
          "quantidade",
          "licitacao_valor",
          "valor_contrato",
          "empenhado_contrato",
          "pago_contrato",
          "data_referencia",
          "limite_dispensa",
          "isento_legalmente",
          "acima_limite",
        ],
      },
      {
        table: "fct_licitacoes_modalidades_metricas",
        description:
          "Mart de métricas de distribuição de modalidades de licitação/contratos.",
        columns: [
          "modalidade_metricas_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "modalidade",
          "quantidade",
          "valor_total",
        ],
      },
      {
        table: "fct_contratos_servicos_vigentes",
        description:
          "Mart de contratos de serviços vigentes agrupados por portal e fornecedor com totais financeiros",
        columns: [
          "contrato_servico_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "contrato_numero",
          "fornecedor_nome",
          "fornecedor_cnpj",
          "objeto_descricao",
          "data_inicio",
          "vencimento_atual",
          "valor_aditado",
          "total_empenhado",
          "total_liquidado",
          "total_pago",
        ],
      },
      {
        table: "fct_contratos",
        description: "Fato de contratos consolidados de todos os portais",
        columns: [
          "contrato_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "contrato_numero",
          "fornecedor_nome",
          "fornecedor_cpf_cnpj",
          "objeto",
          "valor_contrato",
          "valor_aditado",
          "licitacao_numero",
          "modalidade",
          "mes",
          "tipo_obra",
          "numero_obra",
          "fundlegal",
          "empenhado",
          "objeto_completo",
          "data_inicio",
          "vencimento_atual",
          "saldo_a_empenhar",
        ],
      },
      {
        table: "fct_licitacoes",
        description: "Fato de licitações consolidadas de todos os portais",
        columns: [
          "licitacao_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "licitacao_numero",
          "modalidade",
          "objeto",
          "discriminacao",
          "valor",
          "situacao",
          "data_abertura",
          "carona",
        ],
      },
      {
        table: "fct_diarias",
        description: "Fato de diárias consolidadas de todos os portais",
        columns: [
          "id",
          "portal_slug",
          "ano",
          "empresa_id",
          "diaria_id",
          "valor",
          "favorecido",
          "cargo",
          "data",
          "unidade",
          "descricao",
        ],
      },
    ],
  },
  {
    domain: "Orçamento e Pessoal",
    marts: [
      {
        table: "fct_execucao_orcamentaria_metricas",
        description:
          "Mart de métricas agregadas de execução orçamentária por portal, entidade, ano, órgão, unidade, função e subfunção",
        columns: [
          "execucao_orcamentaria_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "orgao_codigo",
          "orgao_nome",
          "unidade_codigo",
          "funcao_codigo",
          "subfuncao_codigo",
          "total_dotacao_atualizada",
          "total_empenhado",
          "total_liquidado",
          "total_pago",
          "saldo_orcamentario",
          "taxa_execucao",
          "alerta_execucao",
        ],
      },
      {
        table: "fct_orcamento_funcional_metricas",
        description:
          "Mart funcional consolidado para orçamento por função/subfunção, portal e exercício",
        columns: [
          "orcamento_funcional_id",
          "portal_slug",
          "empresa_id",
          "ano",
          "funcao_nome",
          "subfuncao_nome",
          "dotacao_atualizada",
          "empenhado",
          "liquidado",
          "pago",
        ],
      },
      {
        table: "fct_pessoal_folha_metricas",
        description:
          "Mart de métricas consolidadas de folha de pagamento, 13º salário, chefias e proventos por portal e empresa.",
        columns: [
          "pessoal_folha_metricas_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "total_folha",
          "total_pago",
        ],
      },
      {
        table: "fct_pessoal_departamento_metricas",
        description:
          "Mart de métricas de folha por departamento (folhas de agrupamento por grupo/descrição).",
        columns: [
          "departamento_metricas_id",
          "portal_slug",
          "ano",
          "empresa_id",
          "descricao",
          "total_pago",
        ],
      },
      {
        table: "fct_pessoal",
        description:
          "Fato de pessoal consolidado de todos os portais (sem chave única por linha)",
        columns: [
          "portal_slug",
          "ano",
          "empresa_id",
          "proventos",
          "categoria_funcional",
          "vinculo",
          "cargo",
          "forma_provimento",
        ],
      },
      {
        table: "dim_orgao",
        description: "Entidades municipais (prefeitura + fundos) por portal",
        columns: ["orgao_id", "portal_slug", "empresa_id", "orgao_nome"],
      },
      {
        table: "dim_elemento_despesa",
        description:
          "Dimensão canônica dos elementos de despesa oficiais (STN/MCASP)",
        columns: ["elemento_codigo", "elemento_descricao", "categoria_macro"],
      },
      {
        table: "dim_natureza_despesa",
        description:
          "Dimensão canônica da estrutura de natureza de despesa (STN/MCASP)",
        columns: [
          "natureza_despesa_codigo",
          "categoria_economica_codigo",
          "categoria_economica_nome",
          "gnd_codigo",
          "gnd_nome",
          "modalidade_codigo",
          "modalidade_nome",
        ],
      },
      {
        table: "dim_funcao_subfuncao",
        description:
          "Dimensão canônica da classificação funcional de despesas (MOG 42/1999)",
        columns: [
          "funcao_subfuncao_codigo",
          "funcao_codigo",
          "funcao_nome",
          "subfuncao_codigo",
          "subfuncao_nome",
        ],
      },
      {
        table: "dim_portais",
        description: "Configurações e metadados dos portais de transparência",
        columns: [
          "portal_slug",
          "display_name",
          "uf",
          "portal_url",
          "base_host",
          "cidade_clean",
          "ano_inicial",
          "empresa_padrao",
          "brasao_asset",
          "data_extracao",
        ],
      },
      {
        table: "dim_date",
        description: "Dimensão calendário diário de 2021 a 2035",
        columns: [
          "data",
          "ano",
          "mes_num",
          "dia",
          "dia_semana",
          "mes_nome",
          "inicio_mes",
          "fim_mes",
          "trimestre",
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
  try {
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
  } catch (_phErr) {}
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
