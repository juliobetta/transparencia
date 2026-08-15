import { google } from "@ai-sdk/google";
import { generateObject, jsonSchema } from "ai";
import { type NextRequest, NextResponse } from "next/server";
import { queryDuckDbParquet } from "@/lib/duckdb-executor";
import { trackMcpToolCall } from "@/lib/mcp/transparencia-mcp";
import { buildLayeredContext } from "@/lib/skills/context-builder";

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

function fmtMoney(val: unknown): string {
  if (val == null) return "R$ 0,00";
  let num = 0;
  if (typeof val === "bigint") {
    num = Number(val);
  } else if (typeof val === "object" && val !== null) {
    const v = val as Record<string, unknown>;
    if (typeof v.doubleValue === "function") {
      num = (v.doubleValue as () => number)();
    } else if ("low" in v && typeof v.low === "number") {
      num = v.low;
    } else {
      num = Number(val);
    }
  } else {
    num = Number(val);
  }

  if (Number.isNaN(num) || !Number.isFinite(num) || Math.abs(num) > 1e14) {
    return "R$ 0,00";
  }

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(num);
}

const assistantOutputSchema = jsonSchema<{
  sql: string;
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
    sql: {
      type: "string",
      description:
        "Consulta SQL DuckDB agregada com CAST(... AS DOUBLE) sobre os marts de transparência pública",
    },
    answer: {
      type: "string",
      description:
        "Explicação amigável em linguagem simples para o cidadão sem mencionar jargões técnicos de infraestrutura ou banco de dados",
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
  required: ["sql", "answer"],
});

export async function POST(req: NextRequest) {
  const startTime = Date.now();
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
    const queryText = message.toLowerCase().trim();

    // 1. Injeção de Contexto em Camadas (Layered Context)
    const systemContext = buildLayeredContext({
      portalSlug,
      year,
      currentRoute,
    });

    // 2. Orquestração LLM via Vercel AI SDK se API KEY estiver presente
    const apiKey =
      process.env.GOOGLE_GENERATIVE_AI_API_KEY || process.env.GEMINI_API_KEY;

    if (apiKey) {
      try {
        const promptText = `${systemContext}\n\nPERGUNTA DO CIDADÃO: "${message}"\n\nResponda devolvendo o JSON estrito com SQL DuckDB seguro e explicação amigável.`;
        const { object } = await generateObject({
          model: google("gemini-1.5-flash"),
          schema: assistantOutputSchema,
          prompt: promptText,
        });

        let queryResults: Record<string, unknown>[] = [];
        if (object.sql) {
          try {
            queryResults = await queryDuckDbParquet(object.sql);
          } catch (_e) {}
        }

        const responsePayload = {
          answer: object.answer,
          metrics: object.metrics,
          chartType: object.chartType || "metric",
          sqlQuery: object.sql,
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

        // Rastreamento de Observabilidade no PostHog ($ai_generation)
        await trackMcpToolCall(
          "assistant_llm_chat",
          {
            input: { message, portalSlug, year, currentRoute },
            output: responsePayload,
            latencyMs: Date.now() - startTime,
          },
          { traceId, model: "gemini-1.5-flash" },
        );

        return NextResponse.json(responsePayload);
      } catch (_llmErr) {}
    }

    // 3. Execução Determinística Fallback inteligente baseada em palavras-chave do usuário
    const searchMatch = message.match(
      /(?:empresa|fornecedor|credor|contrato)\s+([a-zA-Z0-9_-]{2,})/i,
    );
    const searchCompany = searchMatch
      ? searchMatch[1]
      : queryText.length <= 10 && !queryText.includes(" ")
        ? queryText
        : null;

    if (
      searchCompany ||
      queryText.includes("esn") ||
      queryText.includes("contrato") ||
      queryText.includes("pendencia") ||
      queryText.includes("pendência")
    ) {
      const companyTerm =
        searchCompany || (queryText.includes("esn") ? "esn" : "");
      let sql = "";
      if (companyTerm) {
        sql = `SELECT contrato_numero, fornecedor_nome, objeto_descricao, CAST(total_empenhado AS DOUBLE) as empenhado, CAST(total_pago AS DOUBLE) as pago, status_execucao FROM fct_contratos_servicos_vigentes WHERE portal_slug = '${portalSlug}' AND ano = ${year} AND fornecedor_nome ILIKE '%${companyTerm}%'`;
      } else {
        sql = `SELECT contrato_numero, fornecedor_nome, objeto_descricao, CAST(total_empenhado AS DOUBLE) as empenhado, CAST(total_pago AS DOUBLE) as pago, status_execucao FROM fct_contratos_servicos_vigentes WHERE portal_slug = '${portalSlug}' AND ano = ${year} LIMIT 5`;
      }

      const rows = await queryDuckDbParquet<{
        contrato_numero: string;
        fornecedor_nome: string;
        objeto_descricao: string;
        empenhado: number;
        pago: number;
        status_execucao: string;
      }>(sql);

      if (rows.length > 0) {
        const totalEmpenhado = rows.reduce(
          (sum, r) => sum + Number(r.empenhado || 0),
          0,
        );
        const totalPago = rows.reduce((sum, r) => sum + Number(r.pago || 0), 0);
        const firstSupplier = rows[0].fornecedor_nome;
        const mainContract = rows[0].contrato_numero;

        const resData = {
          answer: `No exercício de **${year}**, encontramos **${rows.length} contrato(s)** vinculado(s) ao termo pesquisado (**${firstSupplier}**), com um total empenhado de **${fmtMoney(totalEmpenhado)}** e **${fmtMoney(totalPago)}** pagos (ex: Contrato nº ${mainContract}).`,
          metrics: [
            {
              title: "Contratos Localizados",
              value: String(rows.length),
              variant: "accent",
            },
            {
              title: "Total Empenhado",
              value: fmtMoney(totalEmpenhado),
              variant: "default",
            },
            {
              title: "Total Pago",
              value: fmtMoney(totalPago),
              variant: "success",
            },
          ],
          chartData: rows.map((r) => ({
            label: r.contrato_numero || "Contrato",
            valor: Number(r.pago || 0),
          })),
          chartType: "bar",
          sqlQuery: sql,
        };

        await trackMcpToolCall(
          "assistant_fallback_chat",
          {
            input: { message, portalSlug, year },
            output: resData,
            latencyMs: Date.now() - startTime,
          },
          { traceId },
        );

        return NextResponse.json(resData);
      }
    }

    // Pessoal e Folha
    if (
      queryText.includes("pessoal") ||
      queryText.includes("folha") ||
      queryText.includes("servidor") ||
      queryText.includes("13")
    ) {
      const sql = `SELECT CAST(SUM(total_folha) AS DOUBLE) as total_folha, CAST(SUM(total_pago) AS DOUBLE) as total_pago FROM fct_pessoal_folha_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      const rows = await queryDuckDbParquet<{
        total_folha: number;
        total_pago: number;
      }>(sql);
      const row = rows[0] || { total_folha: 0, total_pago: 0 };

      const folha = Number(row.total_folha || 0);
      const pago = Number(row.total_pago || 0);

      const resData = {
        answer: `No exercício de **${year}**, a folha bruta de pessoal totalizou **${fmtMoney(folha)}**, sendo quitados **${fmtMoney(pago)}** aos servidores municipais.`,
        metrics: [
          { title: "Total Folha", value: fmtMoney(folha), variant: "default" },
          {
            title: "Total Pago Pessoal",
            value: fmtMoney(pago),
            variant: "success",
          },
        ],
        chartData: [
          { label: "Folha Bruta", valor: folha },
          { label: "Pago Pessoal", valor: pago },
        ],
        chartType: "bar",
        sqlQuery: sql,
      };

      await trackMcpToolCall(
        "assistant_fallback_chat",
        {
          input: { message, portalSlug, year },
          output: resData,
          latencyMs: Date.now() - startTime,
        },
        { traceId },
      );

      return NextResponse.json(resData);
    }

    // Fallback Padrão Posição Fiscal
    const sql = `SELECT CAST(SUM(total_arrecadado) AS DOUBLE) as total_arrecadado, CAST(SUM(despesas_pagas) AS DOUBLE) as despesas_pagas, CAST(SUM(saldo_estimado) AS DOUBLE) as saldo_estimado FROM fct_posicao_fiscal_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year} AND (empresa_id = 7 OR empresa_id = '7')`;
    const rows = await queryDuckDbParquet<{
      total_arrecadado: number;
      despesas_pagas: number;
      saldo_estimado: number;
    }>(sql);

    const row = rows[0] || {
      total_arrecadado: 0,
      despesas_pagas: 0,
      saldo_estimado: 0,
    };
    const totalArrecadado = Number(row.total_arrecadado || 0);
    const despesasPagas = Number(row.despesas_pagas || 0);
    const saldo = Number(row.saldo_estimado || totalArrecadado - despesasPagas);

    const defaultRes = {
      answer: `No exercício de **${year}**, a arrecadação da Prefeitura foi de **${fmtMoney(totalArrecadado)}** e as despesas pagas somaram **${fmtMoney(despesasPagas)}**, gerando um saldo de **${fmtMoney(saldo)}**.`,
      metrics: [
        {
          title: "Total Arrecadado",
          value: fmtMoney(totalArrecadado),
          variant: "success",
        },
        {
          title: "Despesas Pagas",
          value: fmtMoney(despesasPagas),
          variant: "default",
        },
        {
          title: "Saldo Estimado",
          value: fmtMoney(saldo),
          variant: saldo >= 0 ? "accent" : "warning",
        },
      ],
      chartData: [
        { label: "Arrecadado", valor: totalArrecadado },
        { label: "Pago", valor: despesasPagas },
      ],
      chartType: "bar",
      sqlQuery: sql,
    };

    await trackMcpToolCall(
      "assistant_fallback_chat",
      {
        input: { message, portalSlug, year },
        output: defaultRes,
        latencyMs: Date.now() - startTime,
      },
      { traceId },
    );

    return NextResponse.json(defaultRes);
  } catch (_error) {
    return NextResponse.json(
      { error: "Ocorreu um erro ao consultar os dados fiscais." },
      { status: 500 },
    );
  }
}
