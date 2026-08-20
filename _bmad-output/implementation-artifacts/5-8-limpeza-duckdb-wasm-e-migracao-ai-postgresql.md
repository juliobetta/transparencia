---
baseline_commit: 05480c1
---

# Story 5.8: Limpeza do DuckDB-WASM e Migração da IA para PostgreSQL

## Status
- **Status:** done
- **Epic:** 5 - Arquitetura Analytics Serverless, Servidor MCP & Assistente Fiscal com Evals
- **Sub-Epic:** 5.8 - Remoção do Executável WASM e Re-alinhamento ao Supabase PostgreSQL
- **Story Key:** 5-8-limpeza-duckdb-wasm-e-migracao-ai-postgresql
- **Last Updated:** 2026-08-20

---

## User Story Statement

**As a** desenvolvedor da plataforma TransparenciaWeb,  
**I want** remover a infraestrutura experimental de DuckDB-WASM em ambiente serverless (Vercel Node.js runtime) e re-alinhar as ferramentas do assistente de IA/MCP para executarem consultas analíticas diretamente sobre o banco PostgreSQL gerenciado no Supabase via `@transparencia/db`,  
**So that** eliminemos instabilidades de cold-start, timeouts de rede (10s), estouros de limite de bundle da Vercel (50MB) e downloads dinâmicos de WASM para `/tmp`, garantindo 100% de estabilidade e baixa latência para o assistente.

---

## Acceptance Criteria

1. **Dado** o arquivo `apps/web/lib/duckdb-executor.ts`,
2. **When** o módulo é refatorado,
3. **Then** todas as referências ao `@duckdb/duckdb-wasm`, `ensureWasmFiles()`, `getDuckDbDistDir()`, downloads para `/tmp` via jsDelivr e pool de conexões com o MotherDuck são totalmente eliminados.
4. **And** a função `queryDuckDbParquet(sql)` é mantida como interface simplificada que invoca `executeRawSql` exposta por `@transparencia/db` sobre o PostgreSQL do Supabase via Kysely (`db.executeQuery(CompiledQuery.raw(sql))`).
5. **And** o arquivo `apps/web/next.config.js` é limpo, removendo `@duckdb/duckdb-wasm` de `serverExternalPackages` e eliminando a chave `outputFileTracingIncludes`.
6. **And** a dependência `@duckdb/duckdb-wasm` é removida de `apps/web/package.json`.
7. **And** a função `executeRawSql` é exposta em `@transparencia/db/src/client.ts` e `packages/db/src/index.ts`.
8. **And** todas as suítes de teste (`pnpm test`) e de compilação (`pnpm build`) continuam 100% limpas e verdes.

---

## Technical Requirements & Architecture Guardrails

### 1. Limpeza de Dependências e Configurações (`apps/web`)
- Remover `@duckdb/duckdb-wasm` do `package.json`.
- Remover `outputFileTracingIncludes` e `@duckdb/duckdb-wasm` do `next.config.js`.

### 2. Camada de Conexão com Banco de Dados (`@transparencia/db`)
- Exportar `executeRawSql` em `@transparencia/db` utilizando Kysely's `CompiledQuery.raw()`.

### 3. Refatoração do Executor de Consulta (`apps/web/lib/duckdb-executor.ts`)
- Substituir o arquivo por uma implementação enxuta que consome `executeRawSql` de `@transparencia/db`.

---

## Tasks / Subtasks

- [x] Task 1: Refatorar `packages/db/src/client.ts` e `packages/db/src/index.ts` para exportar a função `executeRawSql` (AC: #7)
- [x] Task 2: Simplificar `apps/web/lib/duckdb-executor.ts` para invocar `executeRawSql` em vez de WASM/MotherDuck (AC: #1, #2, #3, #4)
- [x] Task 3: Remover a dependência `@duckdb/duckdb-wasm` de `apps/web/package.json` (AC: #6)
- [x] Task 4: Limpar `apps/web/next.config.js` removendo configurações específicas de WASM (AC: #5)
- [x] Task 5: Executar e validar suítes completas de testes e build (`pnpm test` e `pnpm build`) (AC: #8)
