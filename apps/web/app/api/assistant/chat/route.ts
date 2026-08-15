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

function fmtMoney(val: number | null | undefined): string {
  if (val == null || Number.isNaN(Number(val))) return "R$ 0,00";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(val));
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
        "Consulta SQL DuckDB agregada com SUM() sobre os arquivos Parquet (views: fct_posicao_fiscal_metricas, fct_fontes_receita_metricas, fct_historia_saude_metricas, fct_historia_caprem_metricas, fct_licitacoes_gaps_metricas)",
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

Gere a consulta SQL agregada com SUM() para rodar na base de dados fiscais do exercício de ${year}:
Views disponíveis e colunas exatas:
- fct_posicao_fiscal_metricas (columns: portal_slug, ano, SUM(total_arrecadado) as total_arrecadado, SUM(despesas_pagas) as despesas_pagas, SUM(saldo_estimado) as saldo_estimado)
- fct_fontes_receita_metricas (columns: portal_slug, ano, SUM(total_previsto) as total_previsto, SUM(total_arrecadado) as total_arrecadado, SUM(emendas_pix_arrecadado) as emendas_pix_arrecadado)
- fct_historia_saude_metricas (columns: portal_slug, ano, SUM(total_liquidado) as total_liquidado, SUM(total_pago) as total_pago)
- fct_historia_caprem_metricas (columns: portal_slug, ano, SUM(total_empenhado_patronal) as total_empenhado_patronal, SUM(total_pago_patronal) as total_pago_patronal)
- fct_licitacoes_gaps_metricas (columns: portal_slug, ano, SUM(valor_contrato) as total_dispensas, COUNT(*) as qtd_dispensas)

Filtre obrigatoriamente por portal_slug = '${portalSlug}' AND ano = ${year}.
NUNCA esqueça do filtro ano = ${year}.
IMPORTANTE: Na resposta 'answer', informe com clareza os valores do exercício de ${year}. NUNCA mencione termos técnicos como DuckDB, Parquet, R2, SQL ou banco de dados.`,
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

    // 2. Execução Determinística Fallback agregada por SUM(...) no ano selecionado
    if (
      queryText.includes("receita") ||
      queryText.includes("fonte") ||
      queryText.includes("emenda") ||
      queryText.includes("pix")
    ) {
      const sql = `SELECT SUM(total_previsto) as total_previsto, SUM(total_arrecadado) as total_arrecadado, SUM(emendas_pix_arrecadado) as emendas_pix_arrecadado FROM fct_fontes_receita_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
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
        answer: `No exercício de **${year}**, a receita prevista total foi de **${fmtMoney(previsto)}**, com **${fmtMoney(arrecadado)}** arrecadados (sendo **${fmtMoney(emendasPix)}** provenientes de Emendas PIX).`,
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
      const sql = `SELECT SUM(total_liquidado) as total_liquidado, SUM(total_pago) as total_pago FROM fct_historia_saude_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
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
      const sql = `SELECT SUM(total_empenhado_patronal) as total_empenhado_patronal, SUM(total_pago_patronal) as total_pago_patronal FROM fct_historia_caprem_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
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
      const sql = `SELECT SUM(valor_contrato) as total_dispensas, COUNT(*) as qtd_dispensas FROM fct_licitacoes_gaps_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
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

    // Fallback Padrão: Posição Fiscal Agregada por SUM(...) no ano selecionado
    const sql = `SELECT SUM(total_arrecadado) as total_arrecadado, SUM(despesas_pagas) as despesas_pagas, SUM(saldo_estimado) as saldo_estimado FROM fct_posicao_fiscal_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
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
      answer: `No exercício de **${year}**, a arrecadação total foi de **${fmtMoney(totalArrecadado)}** e as despesas pagas somaram **${fmtMoney(despesasPagas)}**, gerando um saldo estimado de **${fmtMoney(saldo)}**.`,
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
