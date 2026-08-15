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
  "fct_posicao_fiscal_metricas",
  "fct_posicao_fiscal_detalhes_metricas",
  "fct_fontes_receita_metricas",
  "fct_historia_saude_metricas",
  "fct_historia_caprem_metricas",
  "fct_licitacoes_gaps_metricas",
  "fct_licitacoes_modalidades_metricas",
  "fct_contratos_servicos_vigentes",
  "fct_execucao_orcamentaria_metricas",
  "fct_despesas_restos_metricas",
  "fct_analise_despesas_metricas",
];

export async function getDuckDbInstance(): Promise<unknown> {
  if (!dbPromise) {
    dbPromise = (async () => {
      try {
        if (typeof window === "undefined") {
          // Ambiente Server-side Node.js (Vercel Functions / Next.js Server)
          // biome-ignore lint/security/noGlobalEval: requer require dinamico para isolar bundle do Turbopack
          const req = eval("require");
          const duckdbNode = req(
            "@duckdb/duckdb-wasm/dist/duckdb-node-blocking.cjs",
          );
          const wasmPath = req.resolve(
            "@duckdb/duckdb-wasm/dist/duckdb-eh.wasm",
          );
          const bundles = {
            mvp: { mainModule: wasmPath, mainWorker: "" },
            eh: { mainModule: wasmPath, mainWorker: "" },
          };
          const logger = new duckdbNode.ConsoleLogger();
          const instance = await duckdbNode.createDuckDB(
            bundles,
            logger,
            duckdbNode.NODE_RUNTIME,
          );
          await instance.instantiate(wasmPath);
          return instance;
        }
        // Ambiente Browser Client-side
        const DUCKDB_BUNDLES = duckdb.getJsDelivrBundles();
        const bundle = await duckdb.selectBundle(DUCKDB_BUNDLES);
        const mainWorker = bundle.mainWorker ?? "";
        const worker = new Worker(mainWorker);
        const logger = new duckdb.ConsoleLogger();
        const instance = new duckdb.AsyncDuckDB(logger, worker);
        await instance.instantiate(bundle.mainModule, bundle.pthreadWorker);
        return instance;
      } catch (err) {
        dbPromise = null;
        throw err;
      }
    })();
  }

  const db = (await dbPromise) as {
    connect: () => Promise<{
      query: (sql: string) => Promise<unknown>;
      close: () => Promise<void>;
    }>;
  };

  if (!initializedViews && db) {
    const conn = await db.connect();
    for (const table of MART_TABLES) {
      const parquetFile = resolveParquetPath(table);
      try {
        await conn.query(
          `CREATE OR REPLACE VIEW ${table} AS SELECT * FROM '${parquetFile.replace(/\\/g, "/")}'`,
        );
      } catch (_err) {}
    }
    await conn.close();
    initializedViews = true;
  }

  return db;
}

export async function queryDuckDbParquet<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  try {
    const db = (await getDuckDbInstance()) as {
      connect: () => Promise<{
        query: (
          sql: string,
        ) => Promise<{ toArray: () => { toJSON: () => T }[] }>;
        close: () => Promise<void>;
      }>;
    };
    const conn = await db.connect();
    const result = await conn.query(sqlQuery);
    await conn.close();
    return result.toArray().map((row: { toJSON: () => T }) => row.toJSON());
  } catch (_err) {
    return [];
  }
}
