import { Kysely, PostgresDialect } from "kysely";
import pg from "pg";
import dotenv from "dotenv";
import path from "path";

// Tenta carregar .env da raiz se process.env.DATABASE_URL não estiver setado
if (!process.env.DATABASE_URL) {
  dotenv.config({ path: path.resolve(__dirname, "../../../.env") });
}

const connectionString =
  process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5544/postgres";

export const db = new Kysely<any>({
  dialect: new PostgresDialect({
    pool: new pg.Pool({
      connectionString,
      max: 10,
    }),
  }),
});
