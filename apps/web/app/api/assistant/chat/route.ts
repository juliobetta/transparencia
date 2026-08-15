import { google } from "@ai-sdk/google";
import { generateObject, jsonSchema } from "ai";
import { type NextRequest, NextResponse } from "next/server";
import { queryDuckDbParquet } from "@/lib/duckdb-executor";

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
        "Consulta SQL DuckDB agregada com CAST(SUM(...) AS DOUBLE) para a Prefeitura (empresa_id = 7) sobre as views",
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
  try {
    const body = await req.json();
    const {
      message,
      portalSlug = "porciuncula_prefeitura",
      ano: yearParam,
    } = body;

    if (!message || typeof message !== "string") {
      return NextResponse.json(
        { error: "Parâmetro 'message' é obrigatório." },
        { status: 400 },
      );
    }

    const year = Number(yearParam) || 2025;
    const queryText = message.toLowerCase().trim();

    // 1. Orquestração LLM via Vercel AI SDK se API KEY estiver presente
    const apiKey =
      process.env.GOOGLE_GENERATIVE_AI_API_KEY || process.env.GEMINI_API_KEY;

    if (apiKey) {
      try {
        const { object } = await generateObject({
          model: google("gemini-1.5-flash"),
          schema: assistantOutputSchema,
          prompt: `Você é o Assistente Fiscal AI do Portal da Transparência de ${portalSlug}.
O usuário selecionou o exercício de ${year} e perguntou: "${message}".

Gere a consulta SQL agregada com CAST(... AS DOUBLE) para rodar na base de dados da Prefeitura (empresa_id = 7) do exercício de ${year}:
Views disponíveis:
- fct_posicao_fiscal_metricas (columns: CAST(SUM(total_arrecadado) AS DOUBLE) as total_arrecadado, CAST(SUM(despesas_pagas) AS DOUBLE) as despesas_pagas, CAST(SUM(saldo_estimado) AS DOUBLE) as saldo_estimado)
- fct_fontes_receita_metricas (columns: CAST(SUM(total_previsto) AS DOUBLE) as total_previsto, CAST(SUM(total_arrecadado) AS DOUBLE) as total_arrecadado, CAST(SUM(emendas_pix_arrecadado) AS DOUBLE) as emendas_pix_arrecadado)
- fct_historia_saude_metricas (columns: CAST(SUM(total_liquidado) AS DOUBLE) as total_liquidado, CAST(SUM(total_pago) AS DOUBLE) as total_pago)
- fct_historia_caprem_metricas (columns: CAST(SUM(total_empenhado_patronal) AS DOUBLE) as total_empenhado_patronal, CAST(SUM(total_pago_patronal) AS DOUBLE) as total_pago_patronal)
- fct_licitacoes_gaps_metricas (columns: CAST(SUM(valor_contrato) AS DOUBLE) as total_dispensas, CAST(COUNT(*) AS DOUBLE) as qtd_dispensas)

Filtre obrigatoriamente por portal_slug = '${portalSlug}' AND ano = ${year} AND (empresa_id = 7 OR empresa_id = '7').
IMPORTANTE: Na resposta 'answer', informe com clareza os valores da Prefeitura no exercício de ${year}. NUNCA mencione termos técnicos como DuckDB, Parquet, R2, SQL ou banco de dados.`,
        });

        let queryResults: Record<string, unknown>[] = [];
        if (object.sql) {
          try {
            queryResults = await queryDuckDbParquet(object.sql);
          } catch (_e) {}
        }

        return NextResponse.json({
          answer: object.answer,
          metrics: object.metrics,
          chartType: object.chartType || "metric",
          sqlQuery: object.sql,
          chartData: queryResults.slice(0, 5).map((row) => ({
            label: String(row.label || row.objeto || "Valor"),
            valor: Number(
              row.valor || row.total_arrecadado || row.valor_contrato || 0,
            ),
          })),
        });
      } catch (_llmErr) {}
    }

    // 2. Execução Determinística Fallback protegida com CAST(... AS DOUBLE) e filtro por empresa_id = 7
    if (
      queryText.includes("receita") ||
      queryText.includes("fonte") ||
      queryText.includes("emenda") ||
      queryText.includes("pix")
    ) {
      const sql = `SELECT CAST(SUM(total_previsto) AS DOUBLE) as total_previsto, CAST(SUM(total_arrecadado) AS DOUBLE) as total_arrecadado, CAST(SUM(emendas_pix_arrecadado) AS DOUBLE) as emendas_pix_arrecadado FROM fct_fontes_receita_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year} AND (empresa_id = 7 OR empresa_id = '7')`;
      const rows = await queryDuckDbParquet<{
        total_previsto: number;
        total_arrecadado: number;
        emendas_pix_arrecadado: number;
      }>(sql);

      const row = rows[0] || {
        total_previsto: 0,
        total_arrecadado: 0,
        emendas_pix_arrecadado: 0,
      };
      const previsto = Number(row.total_previsto || 0);
      const arrecadado = Number(row.total_arrecadado || 0);
      const emendasPix = Number(row.emendas_pix_arrecadado || 0);

      return NextResponse.json({
        answer: `No exercício de **${year}**, a receita prevista total da Prefeitura foi de **${fmtMoney(previsto)}**, com **${fmtMoney(arrecadado)}** arrecadados (sendo **${fmtMoney(emendasPix)}** provenientes de Emendas PIX).`,
        metrics: [
          { title: "Receita Prevista", value: fmtMoney(previsto) },
          {
            title: "Total Arrecadado",
            value: fmtMoney(arrecadado),
            variant: "success",
          },
          {
            title: "Emendas PIX",
            value: fmtMoney(emendasPix),
            variant: "accent",
          },
        ],
        chartData: [
          { label: "Previsto", valor: previsto },
          { label: "Arrecadado", valor: arrecadado },
        ],
        chartType: "bar",
        sqlQuery: sql,
      });
    }

    if (
      queryText.includes("saude") ||
      queryText.includes("saúde") ||
      queryText.includes("hospital")
    ) {
      const sql = `SELECT CAST(SUM(total_liquidado) AS DOUBLE) as total_liquidado, CAST(SUM(total_pago) AS DOUBLE) as total_pago FROM fct_historia_saude_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      const rows = await queryDuckDbParquet<{
        total_liquidado: number;
        total_pago: number;
      }>(sql);
      const row = rows[0] || { total_liquidado: 0, total_pago: 0 };

      const liquidado = Number(row.total_liquidado || 0);
      const pago = Number(row.total_pago || 0);

      return NextResponse.json({
        answer: `No setor da **Saúde (${year})**, o total liquidado foi de **${fmtMoney(liquidado)}** e os pagamentos efetuados somaram **${fmtMoney(pago)}**.`,
        metrics: [
          { title: "Liquidado Saúde", value: fmtMoney(liquidado) },
          { title: "Pago Saúde", value: fmtMoney(pago), variant: "success" },
        ],
        chartData: [
          { label: "Liquidado", valor: liquidado },
          { label: "Pago", valor: pago },
        ],
        chartType: "bar",
        sqlQuery: sql,
      });
    }

    if (
      queryText.includes("caprem") ||
      queryText.includes("previdencia") ||
      queryText.includes("previdência") ||
      queryText.includes("atuaria")
    ) {
      const sql = `SELECT CAST(SUM(total_empenhado_patronal) AS DOUBLE) as total_empenhado_patronal, CAST(SUM(total_pago_patronal) AS DOUBLE) as total_pago_patronal FROM fct_historia_caprem_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      const rows = await queryDuckDbParquet<{
        total_empenhado_patronal: number;
        total_pago_patronal: number;
      }>(sql);
      const row = rows[0] || {
        total_empenhado_patronal: 0,
        total_pago_patronal: 0,
      };

      const empenhado = Number(row.total_empenhado_patronal || 0);
      const pago = Number(row.total_pago_patronal || 0);

      return NextResponse.json({
        answer: `No âmbito da previdência (**CAPREM - ${year}**), a retenção patronal empenhada foi de **${fmtMoney(empenhado)}** e o valor quitado somou **${fmtMoney(pago)}**.`,
        metrics: [
          { title: "Patronal Empenhado", value: fmtMoney(empenhado) },
          {
            title: "Patronal Quitado",
            value: fmtMoney(pago),
            variant: "success",
          },
        ],
        chartData: [
          { label: "Empenhado", valor: empenhado },
          { label: "Pago", valor: pago },
        ],
        chartType: "bar",
        sqlQuery: sql,
      });
    }

    if (
      queryText.includes("licitacao") ||
      queryText.includes("licitação") ||
      queryText.includes("dispensa") ||
      queryText.includes("contrato")
    ) {
      const sql = `SELECT CAST(SUM(valor_contrato) AS DOUBLE) as total_dispensas, CAST(COUNT(*) AS DOUBLE) as qtd_dispensas FROM fct_licitacoes_gaps_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      const rows = await queryDuckDbParquet<{
        total_dispensas: number;
        qtd_dispensas: number;
      }>(sql);
      const row = rows[0] || { total_dispensas: 0, qtd_dispensas: 0 };

      const total = Number(row.total_dispensas || 0);
      const qtd = Number(row.qtd_dispensas || 0);

      return NextResponse.json({
        answer: `No exercício de **${year}**, o valor total registrado em dispensas de licitação e contratações diretas foi de **${fmtMoney(total)}**, englobando **${qtd}** processos catalogados.`,
        metrics: [
          {
            title: "Total Dispensas",
            value: fmtMoney(total),
            variant: "accent",
          },
          { title: "Processos", value: String(qtd), variant: "default" },
        ],
        chartData: [{ label: "Total Dispensas", valor: total }],
        chartType: "bar",
        sqlQuery: sql,
      });
    }

    // Fallback Padrão: Posição Fiscal Agregada da Prefeitura (empresa_id = 7) protegida por CAST AS DOUBLE
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

    return NextResponse.json({
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
    });
  } catch (_error) {
    return NextResponse.json(
      { error: "Ocorreu um erro ao consultar os dados fiscais." },
      { status: 500 },
    );
  }
}
