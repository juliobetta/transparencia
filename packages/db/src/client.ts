import path from "node:path";
import dotenv from "dotenv";
import { Kysely, PostgresDialect } from "kysely";
import pg from "pg";

// Tenta carregar .env da raiz se process.env.DATABASE_URL não estiver setado
if (!process.env.DATABASE_URL) {
  dotenv.config({ path: path.resolve(__dirname, "../../../.env") });
}

const connectionString =
  process.env.DATABASE_URL ||
  "postgresql://postgres:postgres@localhost:5544/postgres";

// Em ambiente serverless (Vercel) cada instância mantém seu próprio pool, então
// um `max` alto multiplicado pelo número de instâncias esgota rapidamente o
// limite de conexões do Postgres gerenciado. As requisições disparam as queries
// sequencialmente, portanto um pool pequeno basta. Configurável via env.
const poolMax = Number(process.env.DATABASE_POOL_MAX) || 5;

const pool = new pg.Pool({
  connectionString,
  max: poolMax,
});

// O Postgres gerenciado encerra conexões ociosas. Quando isso acontece, o `pg`
// emite um evento 'error' no client ocioso; sem este listener ele vira uma
// exceção não tratada que derruba o handler da requisição — mesmo com a query
// envolvida em try/catch. Logamos e deixamos o pool descartar a conexão; a
// próxima query abre uma nova.
pool.on("error", (err) => {
  // biome-ignore lint/suspicious/noConsole: registrar o erro é o objetivo deste handler — em serverless o stderr é coletado pela plataforma.
  console.error("[db] Erro em conexão ociosa do pool Postgres:", err);
});

export const db = new Kysely<any>({
  dialect: new PostgresDialect({
    pool,
  }),
});

export async function closeDb(): Promise<void> {
  await db.destroy();
}
