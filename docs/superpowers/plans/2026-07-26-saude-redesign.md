# Página da Saúde Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Health Page (`apps/web/app/[portalSlug]/saude/page.tsx`) to match the high-fidelity design mockup, expanding `@transparencia/db` health queries and creating reusable UI chart components in `@transparencia/ui`.

**Architecture:** Data fetching and business logic belong exclusively to `@transparencia/db/src/queries/historia_saude.ts`. Visualization components (Donut chart for revenue sources, Bar chart for multi-year trends, KPI cards) are created/exported in `@transparencia/ui`. The Next.js page component (`apps/web/app/[portalSlug]/saude/page.tsx`) acts purely as a presentation layer consuming the typed data.

**Tech Stack:** Next.js (Server Components), TypeScript, Kysely (PostgreSQL queries), Recharts / `@transparencia/ui`, Tailwind CSS.

## Global Constraints

- Mandatory portal filtering: All queries must include `portalSlug` or target enterprise filters.
- Layer separation: No business/accounting logic in `apps/web` components.
- Pinned versions: Exact package versions without `^` or `~`.
- Verification: Run `pnpm test` / `make test/ts` and `pnpm build` / `tsc --noEmit`.

---

### Task 1: Extend `@transparencia/db` Health Query Data Model

**Files:**
- Modify: `packages/db/src/queries/historia_saude.ts`
- Modify: `packages/db/src/index.ts` (if exporting new interfaces)

**Interfaces:**
- Consumes: PostgreSQL Kysely client (`db` from `../client`)
- Produces: `getHistoriaSaude(year: number, empresaIds?: string[] | string | null, portalSlug?: string): Promise<HistoriaSaudeResult>`

- [ ] **Step 1: Update type definitions in `historia_saude.ts`**

```typescript
export interface FontesReceitaSaude {
  uniaoSusPct: number;
  estadoPct: number;
  propriaPct: number;
  repassesPrefeitura: number;
  emendasParlamentares: number;
}

export interface AssistenciaFarmaceuticaSaude {
  medicamentosInsumos: number; // Subfunção 10.303
  judicializacao: number;       // Sentenças judiciais
  hhi: number;                  // Concentração HHI
  hhiClassificacao: string;     // Ex: "moderada a alta"
}

export interface HistoriaSaudeResult {
  orcamento: BudgetSaude;
  fontesReceita: FontesReceitaSaude;
  executionTrend: ExecutionTrendSaude[];
  farmaceutica: AssistenciaFarmaceuticaSaude;
  emendas: EmendaSaude[];
  emendasTotal: number;
}
```

- [ ] **Step 2: Implement SQL queries for `fontesReceita`, `executionTrend`, and `farmaceutica` in `historia_saude.ts`**

Add robust SQL queries with error handling so queries return clean values even on test database environments.

- [ ] **Step 3: Verify TypeScript compilation in `@transparencia/db`**

Run: `pnpm --filter @transparencia/db build` or `pnpm tsc --noEmit`
Expected: PASS with 0 errors

- [ ] **Step 4: Commit**

```bash
git add packages/db/src/queries/historia_saude.ts packages/db/src/index.ts
git commit -m "feat(db): expand getHistoriaSaude query with revenue sources and pharmaceutical data"
```

---

### Task 2: Create UI Chart Components in `@transparencia/ui`

**Files:**
- Create: `packages/ui/src/components/charts/saude-fontes-donut.tsx`
- Create: `packages/ui/src/components/charts/saude-trend-chart.tsx`
- Modify: `packages/ui/src/components/charts/index.ts`
- Modify: `packages/ui/src/index.ts`

**Interfaces:**
- Consumes: `FontesReceitaSaude`, `ExecutionTrendSaude[]`
- Produces: `<SaudeFontesDonut data={fontesReceita} />`, `<SaudeTrendChart data={executionTrend} />`

- [ ] **Step 1: Create `SaudeFontesDonut` component**

Render a Recharts Donut chart with customized legend matching the mockup colors (Green for SUS, Yellow/Gold for Estado, Blue for Receita própria/repasse).

- [ ] **Step 2: Create `SaudeTrendChart` component**

Render a Recharts vertical Bar chart for multi-year empenhos (2020–2025).

- [ ] **Step 3: Export components in `packages/ui/src/index.ts`**

- [ ] **Step 4: Verify build in `@transparencia/ui`**

Run: `pnpm --filter @transparencia/ui build`
Expected: PASS with 0 errors

- [ ] **Step 5: Commit**

```bash
git add packages/ui/src/components/charts/ packages/ui/src/index.ts
git commit -m "feat(ui): add SaudeFontesDonut and SaudeTrendChart visualization components"
```

---

### Task 3: Redesign the Web Page `apps/web/app/[portalSlug]/saude/page.tsx`

**Files:**
- Modify: `apps/web/app/[portalSlug]/saude/page.tsx`

**Interfaces:**
- Consumes: `getHistoriaSaude`, `KPIGrid`, `KPICard`, `SaudeFontesDonut`, `SaudeTrendChart`, `DenseTable`, `getPartialYearPeriod`
- Produces: Updated Health Page Server Component

- [ ] **Step 1: Rewrite `SaudePage` layout**

Structure the page with:
1. Category tag: `TEMAS · EXERCÍCIO {selectedYear}` + Title + Subtitle.
2. Top `KPIGrid` (4 columns): Dotação, Empenhado, Taxa de Execução, Medicamentos e Insumos.
3. Section "O que entrou no Fundo": `SaudeFontesDonut` on left card, Repasses da Prefeitura and Emendas Parlamentares on right cards.
4. Section "Empenhado ano a ano": Full width card with `SaudeTrendChart`.
5. Section "Insumos e assistência farmacêutica": 3 KPI Cards (Medicamentos, Judicialização, Concentração HHI).
6. Section "Emendas Parlamentares Destinadas à Saúde": `DenseTable` of emendas.

- [ ] **Step 2: Verify page build and typechecking**

Run: `pnpm --filter web build`
Expected: PASS with 0 errors

- [ ] **Step 3: Commit**

```bash
git add apps/web/app/\[portalSlug\]/saude/page.tsx
git commit -m "feat(web): redesign health page to match high-fidelity mockup layout"
```

---

### Task 4: Final Parity and Quality Assurance Verification

- [ ] **Step 1: Run TypeScript typecheck across all workspace packages**

Run: `pnpm build`
Expected: PASS with 0 errors

- [ ] **Step 2: Run test suite**

Run: `pnpm test`
Expected: PASS

- [ ] **Step 3: Commit final adjustments if any**

```bash
git commit --allow-empty -m "chore(saude): complete health page redesign and verification"
```
