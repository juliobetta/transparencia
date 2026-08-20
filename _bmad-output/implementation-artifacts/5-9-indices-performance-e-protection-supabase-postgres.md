---
baseline_commit: d73d332
---

# Story 5.9: Otimização de Índices e Performance no Supabase PostgreSQL

## Status
- **Status:** done
- **Epic:** 5 - Arquitetura Analytics Serverless, Servidor MCP & Assistente Fiscal com Evals
- **Sub-Epic:** 5.9 - Isolamento de Roles, Índices de Busca e Proteção por Timeout no Supabase
- **Story Key:** 5-9-indices-performance-e-protection-supabase-postgres
- **Last Updated:** 2026-08-20

---

## User Story Statement

**As a** engenheiro de banco de dados e arquiteto de dados,  
**I want** criar o script de migração SQL (`elt/migrations/001_setup_ai_roles_indices.sql`) ativando as extensões `unaccent` e `pg_trgm`, definindo as roles dedicadas (`transparencia_web_reader`, `transparencia_ai_anon`, `transparencia_ai_user`) com seus respectivos `statement_timeout` (15s, 3s, 7s) e criando índices expressionais em `unaccent(lower(...))` e GIN trgm nas tabelas fato/dimensão principais,  
**So that** buscas textuais do assistente de IA sejam executadas em milissegundos e consultas pesadas/abusivas do agente anônimo sejam abortadas em 3 segundos sem afetar os dashboards da web.

---

## Acceptance Criteria

1. **Dado** o banco de dados PostgreSQL (local e Supabase),
2. **When** o script de migração `elt/migrations/001_setup_ai_roles_indices.sql` for executado,
3. **Then** as extensões `unaccent` e `pg_trgm` são ativadas (`CREATE EXTENSION IF NOT EXISTS`).
4. **And** as roles `transparencia_web_reader`, `transparencia_ai_anon` e `transparencia_ai_user` são criadas com logins e privilégios restritos de `SELECT` no schema `public`.
5. **And** a role `transparencia_web_reader` tem o parâmetro `statement_timeout` configurado para `15s`.
6. **And** a role `transparencia_ai_anon` tem o parâmetro `statement_timeout` configurado para `3s` (3000ms).
7. **And** a role `transparencia_ai_user` tem o parâmetro `statement_timeout` configurado para `7s` (7000ms).
8. **And** são criados índices expressionais btree em `unaccent(lower(...))` para as colunas `nome_credor` em `fct_despesas`, `objeto` em `fct_licitacoes` e `nome_credor` em `dim_credor`.
9. **And** são criados índices GIN `pg_trgm` para acelerar buscas parciais em `descricao_despesa` em `fct_despesas` e `objeto` em `fct_contratos`.
10. **And** todas as suítes de validação (`pnpm test` e `pnpm build`) continuam 100% limpas e aprovadas.

---

## Technical Requirements & Architecture Guardrails

### 1. Script de Migração SQL (`elt/migrations/001_setup_ai_roles_indices.sql`)
- Extensões PostgreSQL: `unaccent`, `pg_trgm`.
- Definição de Roles & Timeouts via `ALTER ROLE ... SET statement_timeout`.
- Expressional Indexes cumprindo a Regra 11 de `AGENTS.md` (`unaccent(lower(...))`).

### 2. Validação & Compatibilidade (`@transparencia/db`)
- Testes de integração via Kysely validando resiliência a timeouts.

---

## Tasks / Subtasks

- [x] Task 1: Criar o script de migração `elt/migrations/001_setup_ai_roles_indices.sql` com extensões, roles, timeouts e índices (AC: #3, #4, #5, #6, #7, #8, #9)
- [x] Task 2: Documentar as instruções de aplicação do script no Supabase Dashboard / CLI
- [x] Task 3: Executar a suíte de testes e validação de build (`pnpm test` e `pnpm build`) (AC: #10)

