import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

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

function getDuckDbDistDir(): string {
  const candidateBasePaths = [
    path.resolve(process.cwd(), "apps/web/package.json"),
    path.resolve(process.cwd(), "package.json"),
    path.resolve(process.cwd(), "node_modules"),
  ];

  for (const basePath of candidateBasePaths) {
    try {
      const customRequire = createRequire(basePath);
      const cjsPath = customRequire.resolve(
        "@duckdb/duckdb-wasm/dist/duckdb-node-blocking.cjs",
      );
      const distDir = path.dirname(cjsPath);
      if (fs.existsSync(path.join(distDir, "duckdb-eh.wasm"))) {
        return distDir;
      }
    } catch {
      // try next candidate
    }
  }

  try {
    const customRequire = createRequire(import.meta.url);
    const cjsPath = customRequire.resolve(
      "@duckdb/duckdb-wasm/dist/duckdb-node-blocking.cjs",
    );
    const distDir = path.dirname(cjsPath);
    if (fs.existsSync(path.join(distDir, "duckdb-eh.wasm"))) {
      return distDir;
    }
  } catch {
    // try fallback paths
  }

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

  if (fs.existsSync(webNodeModules)) return webNodeModules;
  if (fs.existsSync(rootNodeModules)) return rootNodeModules;

  const pnpmDir = path.join(rootPath, "node_modules", ".pnpm");
  if (fs.existsSync(pnpmDir)) {
    try {
      const entries = fs.readdirSync(pnpmDir);
      const duckdbPkg = entries.find((e) =>
        e.startsWith("@duckdb+duckdb-wasm@"),
      );
      if (duckdbPkg) {
        const pnpmDist = path.join(
          pnpmDir,
          duckdbPkg,
          "node_modules",
          "@duckdb",
          "duckdb-wasm",
          "dist",
        );
        if (fs.existsSync(pnpmDist)) return pnpmDist;
      }
    } catch {
      // ignore
    }
  }

  return webNodeModules;
}

function isFileReadable(filePath: string): boolean {
  try {
    const fd = fs.openSync(filePath, "r");
    fs.closeSync(fd);
    return true;
  } catch {
    return false;
  }
}

async function ensureWasmFiles(distDir: string): Promise<{
  wasmPath: string;
  workerPath: string;
}> {
  const localWasm = path.join(distDir, "duckdb-eh.wasm");
  const localWorker = path.join(distDir, "duckdb-node-eh.worker.cjs");

  if (isFileReadable(localWasm) && isFileReadable(localWorker)) {
    return { wasmPath: localWasm, workerPath: localWorker };
  }

  const tmpDir = path.join("/tmp", "duckdb-wasm");
  const tmpWasm = path.join(tmpDir, "duckdb-eh.wasm");
  const tmpWorker = path.join(tmpDir, "duckdb-node-eh.worker.cjs");

  if (isFileReadable(tmpWasm) && isFileReadable(tmpWorker)) {
    return { wasmPath: tmpWasm, workerPath: tmpWorker };
  }

  fs.mkdirSync(tmpDir, { recursive: true });

  const cdnBase =
    "https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@1.28.0/dist/";

  if (!isFileReadable(tmpWasm)) {
    const res = await fetch(`${cdnBase}duckdb-eh.wasm`);
    if (!res.ok) {
      throw new Error(
        `Falha ao baixar duckdb-eh.wasm do CDN: ${res.status} ${res.statusText}`,
      );
    }
    const buf = Buffer.from(await res.arrayBuffer());
    fs.writeFileSync(tmpWasm, buf);
  }

  if (!isFileReadable(tmpWorker)) {
    const res = await fetch(`${cdnBase}duckdb-node-eh.worker.cjs`);
    if (!res.ok) {
      throw new Error(
        `Falha ao baixar duckdb-node-eh.worker.cjs do CDN: ${res.status} ${res.statusText}`,
      );
    }
    const buf = Buffer.from(await res.arrayBuffer());
    fs.writeFileSync(tmpWorker, buf);
  }

  return { wasmPath: tmpWasm, workerPath: tmpWorker };
}

export async function getDuckDbInstance(): Promise<unknown> {
  if (dbPromise) return dbPromise;

  dbPromise = (async () => {
    if (typeof window === "undefined") {
      const distDir = getDuckDbDistDir();
      const customRequire = createRequire(
        path.join(distDir, "duckdb-node-blocking.cjs"),
      );
      const duckdbNode = customRequire(
        path.join(distDir, "duckdb-node-blocking.cjs"),
      );

      const { wasmPath, workerPath } = await ensureWasmFiles(distDir);

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
    const duckdb = await import("@duckdb/duckdb-wasm");
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

async function queryMotherDuck<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  const token =
    process.env.MOTHER_DUCK_MOTHERDUCK_TOKEN || process.env.MOTHERDUCK_TOKEN;
  if (!token) {
    throw new Error(
      "MotherDuck token não configurado em MOTHER_DUCK_MOTHERDUCK_TOKEN",
    );
  }

  const database =
    process.env.MOTHERDUCK_DATABASE ||
    process.env.MOTHER_DUCK_DATABASE ||
    "my_db";

  // Prepara declarações de macro unaccent e VIEWs para as tabelas apontando para o R2/S3
  const prepStatements: string[] = [
    "CREATE MACRO IF NOT EXISTS unaccent(str) AS strip_accents(str);",
  ];

  for (const table of MART_TABLES) {
    if (sqlQuery.includes(table)) {
      const parquetPath = resolveParquetPath(table);
      prepStatements.push(
        `CREATE VIEW IF NOT EXISTS ${table} AS SELECT * FROM read_parquet('${parquetPath}');`,
      );
    }
  }

  const fullQuery = `${prepStatements.join("\n")}\n${sqlQuery}`;

  const res = await fetch("https://api.motherduck.com/v1/sql", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      query: fullQuery,
      database: database,
    }),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Erro na API do MotherDuck (${res.status}): ${errText}`);
  }

  const json = (await res.json()) as {
    rows?: Record<string, unknown>[];
    data?: Record<string, unknown>[];
    results?: { rows?: Record<string, unknown>[] }[];
  };

  const rawRows = json.rows || json.data || json.results?.[0]?.rows || [];
  return rawRows as T[];
}

export async function queryDuckDbParquet<T = Record<string, unknown>>(
  sqlQuery: string,
): Promise<T[]> {
  if (
    process.env.MOTHER_DUCK_MOTHERDUCK_TOKEN ||
    process.env.MOTHERDUCK_TOKEN
  ) {
    return queryMotherDuck<T>(sqlQuery);
  }

  const db = (await getDuckDbInstance()) as {
    connect: () => Promise<{
      query: (sql: string) => Promise<{ toArray: () => unknown[] }>;
      close: () => Promise<void>;
    }>;
  };
  const conn = await db.connect();

  try {
    if (!initializedViews) {
      // Registrar macro unaccent para compatibilidade 100% com sintaxe PostgreSQL
      await conn.query(
        "CREATE MACRO IF NOT EXISTS unaccent(str) AS strip_accents(str)",
      );

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
