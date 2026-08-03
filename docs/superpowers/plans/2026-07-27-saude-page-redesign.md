# Redesign da Página da Saúde Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o novo design da página da Saúde (`/[portalSlug]/saude`), incluindo o Hero narrativo, a seção de contratações (carona/licitações) e a visão detalhada de emendas parlamentares.

**Architecture:** A inteligência fiscal e agregamento SQL pertencem ao `@transparencia/db/src/queries/historia_saude.ts`. A camada de visualização em `@transparencia/ui` exporta componentes modulares que utilizam os tipos e dados do backend Kysely e são renderizados na rota `apps/web/app/[portalSlug]/saude/page.tsx`.

**Tech Stack:** Next.js (App Router), React, TypeScript, Kysely (PostgreSQL), TailwindCSS.

## Global Constraints

- **Breadcrumb**: Utilizar a classe `inline-block font-semibold text-accent text-xs uppercase tracking-wider`.
- **Navegação**: Utilizar o componente `Link` de `next/link` no lugar da tag nativa `<a>`.
- **KPIs**: Utilizar exclusivamente os componentes `KPICard` e `KPIGrid` da `@transparencia/ui`.
- **Portal Slug**: Todas as queries em `@transparencia/db` devem manter isolamento multi-tenant por `portalSlug`/`empresaIds`.
- **Formatting**: Sem alinhamento extra por espaços em queries SQL.

---

### Task 1: Expansão dos Dados Fiscais da Saúde (`@transparencia/db`)

**Files:**
- Modify: `packages/db/src/queries/historia_saude.ts`
- Modify: `packages/db/src/__tests__/parity.test.ts`

**Interfaces:**
- Consumes: `SAUDE_EMPRESA`, `db` client, `sql` Kysely template.
- Produces: `HistoriaSaudeResult` contendo `orcamento`, `fontesReceita`, `executionTrend`, `farmaceutica`, `licitacoesSaude`, `emendasStats`.

- [ ] **Step 1: Escrever teste de paridade atualizado para `getHistoriaSaude`**

Adicionar verificações dos novos campos (`liquidado`, `pago`, `contratosVinculadosCount`, `fornecedoresAtivosCount`, `licitacoesSaude`, `emendasStats`) no arquivo `packages/db/src/__tests__/parity.test.ts`.

- [ ] **Step 2: Executar teste de paridade e verificar falha**

Run: `pnpm test parity.test.ts`
Expected: FAIL indicando propriedades ausentes no retorno.

- [ ] **Step 3: Implementar novos seletores SQL e agregação em `historia_saude.ts`**

Adicionar seletores para `liquidado`, `pago`, contagem de contratos (`fct_contratos`), fornecedores únicos com movimentação (`fct_despesas_por_fornecedor`), modalidades de licitação e totais de emendas.

```typescript
export interface LicitacaoModalidadeItem {
  nome: string;
  valor: number;
  pct: number;
}

export interface LicitacoesSaudeResult {
  adesaoCaronaCount: number;
  adesaoCaronaValor: number;
  empenhosAtaExternaCount: number;
  pagoAtaExternaValor: number;
  modalidades: LicitacaoModalidadeItem[];
}

export interface EmendasStatsSaude {
  totalAutorizado: number;
  totalEmpenhado: number;
  taxaEmpenho: number;
  maiorEmenda: number;
  lista: EmendaSaude[];
}
```

- [ ] **Step 4: Executar testes de paridade e garantir que passam**

Run: `pnpm test parity.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/db/src/queries/historia_saude.ts packages/db/src/__tests__/parity.test.ts
git commit -m "feat(db): expand getHistoriaSaude with liquidado, pago, licitacoes and emendas stats"
```

---

### Task 2: Componentes UI de Saúde (`@transparencia/ui`)

**Files:**
- Create: `packages/ui/src/components/saude-hero-section.tsx`
- Create: `packages/ui/src/components/saude-contratacao-section.tsx`
- Create: `packages/ui/src/components/saude-emendas-section.tsx`
- Modify: `packages/ui/src/index.ts`

**Interfaces:**
- Consumes: Tipos de `HistoriaSaudeResult` de `@transparencia/db`, `KPICard`, `KPIGrid`, `DenseTable`, `fmtCompact`, `fmtCurrency`.
- Produces: `SaudeHeroSection`, `SaudeContratacaoSection`, `SaudeEmendasSection`.

- [ ] **Step 1: Criar o componente `SaudeHeroSection`**

Implementar layout responsivo com breadcrumb padrão, título narrativo, caixa lateral de progresso (`Empenhado → Liquidado → Pago → Medicamentos`) e `KPIGrid` com 4 `KPICard`s.

- [ ] **Step 2: Criar o componente `SaudeContratacaoSection`**

Implementar a seção "Como o Fundo contrata", integrando banner de alerta âmbar para adesões a ata, 4 `KPICard`s, link utilizando Next.js `Link` e gráfico de barras para distribuição por modalidades.

- [ ] **Step 3: Criar o componente `SaudeEmendasSection`**

Implementar a seção "Emendas parlamentares destinadas à Saúde", integrando banner vermelho/salmão de alerta sobre taxa de empenho, 4 `KPICard`s e `DenseTable` com linha de total em destaque.

- [ ] **Step 4: Exportar componentes em `packages/ui/src/index.ts`**

Adicionar exportações dos novos componentes.

- [ ] **Step 5: Validar a tipagem dos pacotes UI**

Run: `pnpm --filter @transparencia/ui build`
Expected: PASS sem erros de compilação.

- [ ] **Step 6: Commit**

```bash
git add packages/ui/src/components/saude-hero-section.tsx packages/ui/src/components/saude-contratacao-section.tsx packages/ui/src/components/saude-emendas-section.tsx packages/ui/src/index.ts
git commit -m "feat(ui): add SaudeHeroSection, SaudeContratacaoSection and SaudeEmendasSection components"
```

---

### Task 3: Montagem da Página da Saúde (`apps/web`)

**Files:**
- Modify: `apps/web/app/[portalSlug]/saude/page.tsx`

**Interfaces:**
- Consumes: `getHistoriaSaude` de `@transparencia/db`, `SaudeHeroSection`, `SaudeFontesDonut`, `SaudeTrendChart`, `SaudeContratacaoSection`, `KPICard`, `KPIGrid`, `SaudeEmendasSection`.
- Produces: Rota da página da Saúde completa com 6 seções sequenciais.

- [ ] **Step 1: Atualizar `apps/web/app/[portalSlug]/saude/page.tsx`**

Integrar as 6 seções na ordem exata definida:
1. `SaudeHeroSection`
2. O que entrou no fundo
3. Empenhado no ano (`SaudeTrendChart`)
4. `SaudeContratacaoSection`
5. Insumos e assistência farmacêutica
6. `SaudeEmendasSection`

- [ ] **Step 2: Executar build e typecheck geral do projeto**

Run: `pnpm build`
Expected: PASS com 0 erros de compilação.

- [ ] **Step 3: Commit**

```bash
git add apps/web/app/[portalSlug]/saude/page.tsx
git commit -m "feat(web): assemble redesigned saude page with 6 ordered sections"
```
