import { NextResponse } from "next/server";
import { queryDuckDbParquet } from "@/lib/duckdb-executor";
import { FISCAL_TAXONOMY, trackMcpToolCall } from "@/lib/mcp/transparencia-mcp";

export async function GET() {
  return NextResponse.json({
    name: "transparencia-mcp",
    version: "1.0.0",
    description: "Servidor MCP de Transparência Fiscal Pública Municipal",
    taxonomy: FISCAL_TAXONOMY,
    tools: [
      {
        name: "list_marts_taxonomia",
        description: "Lista a taxonomia dos 25 marts Parquet.",
      },
      {
        name: "get_mart_schema",
        description: "Retorna a estrutura de colunas de um mart Parquet.",
      },
      {
        name: "query_duckdb_mart",
        description: "Executa consultas SQL analíticas em DuckDB.",
      },
    ],
  });
}

export async function POST(request: Request) {
  const startTime = Date.now();

  try {
    const body = await request.json();
    const { tool, args, trace_id: traceId } = body;

    if (!tool) {
      return NextResponse.json(
        { error: "Parâmetro 'tool' é obrigatório." },
        { status: 400 },
      );
    }

    if (tool === "list_marts_taxonomia") {
      const domainFilter = (args?.domain as string | undefined)?.toLowerCase();
      const result = domainFilter
        ? FISCAL_TAXONOMY.filter((t) =>
            t.domain.toLowerCase().includes(domainFilter),
          )
        : FISCAL_TAXONOMY;

      await trackMcpToolCall(
        tool,
        {
          input: args || {},
          output: result,
          latencyMs: Date.now() - startTime,
        },
        { traceId },
      );
      return NextResponse.json({ result });
    }

    if (tool === "get_mart_schema") {
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
        error: `Tabela '${tableName}' não encontrada.`,
      };
      await trackMcpToolCall(
        tool,
        {
          input: args || {},
          output: result,
          latencyMs: Date.now() - startTime,
        },
        { traceId },
      );
      return NextResponse.json({ result });
    }

    if (tool === "query_duckdb_mart") {
      const sqlQuery = args?.sql_query as string;
      if (!sqlQuery || !/^\s*(SELECT|WITH)\b/i.test(sqlQuery)) {
        return NextResponse.json(
          { error: "Apenas consultas SELECT/WITH são permitidas." },
          { status: 400 },
        );
      }

      const rows = await queryDuckDbParquet(sqlQuery);
      const result = { row_count: rows.length, data: rows };
      await trackMcpToolCall(
        tool,
        {
          input: args || {},
          output: result,
          latencyMs: Date.now() - startTime,
        },
        { traceId },
      );

      return NextResponse.json({ result });
    }

    return NextResponse.json(
      { error: `Ferramenta '${tool}' não suportada.` },
      { status: 404 },
    );
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
