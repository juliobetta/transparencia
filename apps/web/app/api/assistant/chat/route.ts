import { type NextRequest, NextResponse } from "next/server";
import { executeReActAgent } from "@/lib/agent/react-engine";
import { queryDuckDbParquet } from "@/lib/duckdb-executor";
import { trackMcpToolCall } from "@/lib/mcp/transparencia-mcp";

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

    // 1. Orquestração com Agente ReAct + Auto-Correção se a API Key estiver presente
    const apiKey =
      process.env.GOOGLE_GENERATIVE_AI_API_KEY || process.env.GEMINI_API_KEY;

    if (apiKey) {
      try {
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
      } catch (_llmErr) {}
    }

    // 2. Execução Determinística Fallback inteligente baseada em palavras-chave do usuário

    // A. CAPREM / Previdência Municipal / Aportes / Patronal
    if (
      queryText.includes("caprem") ||
      queryText.includes("previdencia") ||
      queryText.includes("previdência") ||
      queryText.includes("aporte") ||
      queryText.includes("patronal") ||
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

      const resData = {
        answer: `No âmbito da previdência municipal (**CAPREM - ${year}**), a retenção e aportes patronais empenhados somaram **${fmtMoney(empenhado)}**, sendo quitados **${fmtMoney(pago)}**.`,
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

    // B. Saúde Pública
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

      const resData = {
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

    // C. Receitas e Fontes
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

      const resData = {
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

    // D. Licitações e Dispensas
    if (
      queryText.includes("licitacao") ||
      queryText.includes("licitação") ||
      queryText.includes("dispensa")
    ) {
      const sql = `SELECT CAST(SUM(valor_contrato) AS DOUBLE) as total_dispensas, CAST(COUNT(*) AS DOUBLE) as qtd_dispensas FROM fct_licitacoes_gaps_metricas WHERE portal_slug = '${portalSlug}' AND ano = ${year}`;
      const rows = await queryDuckDbParquet<{
        total_dispensas: number;
        qtd_dispensas: number;
      }>(sql);
      const row = rows[0] || { total_dispensas: 0, qtd_dispensas: 0 };

      const total = Number(row.total_dispensas || 0);
      const qtd = Number(row.qtd_dispensas || 0);

      const resData = {
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

    // E. Busca por Fornecedor / Empresa / Contrato específico
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

    // F. Pessoal e Folha
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
