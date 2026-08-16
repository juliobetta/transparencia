import fs from "node:fs";
import path from "node:path";
import * as duckdb from "@duckdb/duckdb-wasm";

let dbPromise: Promise<unknown> | null = null;
let initializedViews = false;

function resolveParquetPath(tableName: string): string {
  const s3Endpoint = process.env.S3_ENDPOINT_URL || process.env.R2_ENDPOINT_URL;
  const s3Bucket =
    process.env.S3_BUCKET || process.env.R2_BUCKET || "transparencia-marts";

  if (s3Endpoint) {
    return `${s3Endpoint}/${s3Bucket}/${tableName}.parquet`;
  }

  const rootPath = process.cwd().replace(/\/apps\/web$/, "");
  const localTarget = path.join(
    rootPath,
    "target",
    "parquet",
    `${tableName}.parquet`,
  );
  const eltTarget = path.join(
    rootPath,
    "elt",
    "transform",
    "target",
    "parquet",
    `${tableName}.parquet`,
  );
  const dockerTarget = path.join(
    rootPath,
    "docker",
    "volumes",
    "minio",
    "transparencia-marts",
    `${tableName}.parquet`,
  );

  if (fs.existsSync(localTarget)) return localTarget;
  if (fs.existsSync(eltTarget)) return eltTarget;
  if (fs.existsSync(dockerTarget)) return dockerTarget;

  return localTarget;
}

const MART_TABLES = [
  "dim_credor",
  "dim_date",
  "dim_elemento_despesa",
  "dim_funcao_subfuncao",
  "dim_metadata",
  "dim_natureza_despesa",
  "dim_orgao",
  "dim_portais",
  "fct_analise_despesas_metricas",
  "fct_caprem_cadprev_metricas",
  "fct_caprem_entidades_metricas",
  "fct_caprem_natureza_metricas",
  "fct_caprem_tendencia_atuarial_metricas",
  "fct_contratos",
  "fct_contratos_servicos_vigentes",
  "fct_despesas",
  "fct_despesas_diarias_metricas",
  "fct_despesas_fornecedores_metricas",
  "fct_despesas_por_fornecedor",
  "fct_despesas_por_orgao",
  "fct_despesas_por_unidade",
  "fct_despesas_restos_metricas",
  "fct_diarias",
  "fct_emendas",
  "fct_execucao_orcamentaria_metricas",
  "fct_fontes_receita_metricas",
  "fct_historia_caprem_metricas",
  "fct_historia_saude_metricas",
  "fct_licitacoes",
  "fct_licitacoes_metricas",
  "fct_licitacoes_modalidades_metricas",
  "fct_orcamento_funcional_metricas",
  "fct_pessoal",
  "fct_pessoal_departamento_metricas",
  "fct_pessoal_folha_metricas",
  "fct_posicao_fiscal_detalhes_metricas",
  "fct_posicao_fiscal_metricas",
  "fct_receita_extra_orcamentaria",
  "fct_receitas",
  "fct_transferencias",
];

export async function getDuckDbInstance(): Promise<unknown> {
  if (dbPromise) return dbPromise;

  dbPromise = (async () => {
    if (typeof window === "undefined") {
      // Server-side Node.js CJS require to avoid Turbopack bundle errors
      // biome-ignore lint/security/noGlobalEval: server-side requirement
      const duckdbNode = eval("require")(
        "@duckdb/duckdb-wasm/dist/duckdb-node-blocking.cjs",
      );

      const rootPath = process.cwd().replace(/\/apps\/web$/, "");
      const webNodeModules = path.join(
        rootPath,
        "apps",
        "web",
        "node_modules",
        "@duckdb",
        "duckdb-wasm",
        "dist",
      );
      const rootNodeModules = path.join(
        rootPath,
        "node_modules",
        "@duckdb",
        "duckdb-wasm",
        "dist",
      );
      const distDir = fs.existsSync(webNodeModules)
        ? webNodeModules
        : rootNodeModules;

      const wasmPath = path.join(distDir, "duckdb-eh.wasm");
      const workerPath = path.join(distDir, "duckdb-node-eh.worker.cjs");

      const bundles = {
        eh: {
          mainModule: wasmPath,
          mainWorker: workerPath,
        },
      };

      const logger = new duckdbNode.ConsoleLogger();
      const db = await duckdbNode.createDuckDB(
        bundles,
        logger,
        duckdbNode.NODE_RUNTIME,
      );
      await db.instantiate();
      return db;
    }

    // Client-side browser bundle
    const JSDELIVR_BUNDLES = duckdb.getJsDelivrBundles();
    const bundle = await duckdb.selectBundle(JSDELIVR_BUNDLES);

    const workerUrl = URL.createObjectURL(
      new Blob([`importScripts('${bundle.mainWorker}');`], {
        type: "text/javascript",
      }),
    );

    const worker = new Worker(workerUrl);
    const logger = new duckdb.ConsoleLogger();
    const db = new duckdb.AsyncDuckDB(logger, worker);
    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    URL.revokeObjectURL(workerUrl);
    return db;
  })();

  return dbPromise;
}

export async function queryDuckDbParquet<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  const db = (await getDuckDbInstance()) as {
    connect: () => Promise<{
      query: (sql: string) => Promise<{ toArray: () => unknown[] }>;
      close: () => Promise<void>;
    }>;
  };
  const conn = await db.connect();

  try {
    if (!initializedViews) {
      for (const table of MART_TABLES) {
        const parquetPath = resolveParquetPath(table);
        await conn.query(
          `CREATE VIEW IF NOT EXISTS ${table} AS SELECT * FROM read_parquet('${parquetPath}')`,
        );
      }
      initializedViews = true;
    }

    const result = await conn.query(sqlQuery);
    const rawRows = result.toArray() as Record<string, unknown>[];

    // Converter HugeInt e BigInt de volta para Number/String nativo seguro
    const sanitizedRows = rawRows.map((row) => {
      const cleanObj: Record<string, unknown> = {};
      for (const [key, val] of Object.entries(row)) {
        if (val == null) {
          cleanObj[key] = val;
        } else if (typeof val === "bigint") {
          cleanObj[key] = Number(val);
        } else if (typeof val === "object") {
          const obj = val as Record<string, unknown>;
          if (typeof obj.doubleValue === "function") {
            cleanObj[key] = (obj.doubleValue as () => number)();
          } else if ("low" in obj && typeof obj.low === "number") {
            cleanObj[key] = obj.low;
          } else {
            cleanObj[key] = val;
          }
        } else {
          cleanObj[key] = val;
        }
      }
      return cleanObj as T;
    });

    return sanitizedRows;
  } finally {
    await conn.close();
  }
}
