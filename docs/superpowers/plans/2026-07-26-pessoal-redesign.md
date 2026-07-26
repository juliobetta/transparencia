# Redesign da Página Pessoal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the Pessoal & Vencimentos page to feature a standardized header, 3 key KPI cards (Folha/RCL %, Efetivos nas Chefias %, Total Pago em Folha), a 5-year historical bar chart with LRF reference limit lines (54%, 51.3%, 48.6%), and a 13º Salário execution card with progress bar.

**Architecture:** Create `FolhaLrfHistoryChart` and `DecimoTerceiroCard` UI components in `packages/ui`, export them, and assemble `apps/web/app/[portalSlug]/pessoal/page.tsx` using typed queries from `@transparencia/db`.

**Tech Stack:** Next.js (App Router), React, Tailwind CSS, TypeScript, `@transparencia/ui`, `@transparencia/db`.

## Global Constraints
- Strictly follow DRY architecture (presentation layer imports typed data from `@transparencia/db`).
- Visual design must match existing portal standards (`text-accent`, `font-serif`, `text-slate-900`, etc.).
- No syntax or TypeScript errors (`pnpm build` / `make test/ts`).

---

### Task 1: Create `FolhaLrfHistoryChart` component in `packages/ui`

**Files:**
- Create: `packages/ui/src/components/charts/folha-lrf-history-chart.tsx`
- Modify: `packages/ui/src/index.ts`

**Interfaces:**
- Consumes: `FolhaVsServicosRecord[]` from `@transparencia/db` (or array of `{ ano: number; percentualFolha: number }`).
- Produces: `FolhaLrfHistoryChart` React component.

- [ ] **Step 1: Create `folha-lrf-history-chart.tsx`**

```tsx
import React from "react";

export interface FolhaHistoryItem {
  ano: number;
  percentualFolha: number;
  isCurrentYear?: boolean;
}

interface FolhaLrfHistoryChartProps {
  data: FolhaHistoryItem[];
}

export function FolhaLrfHistoryChart({ data }: FolhaLrfHistoryChartProps) {
  const maxPercent = 60; // Max scale for chart height

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900 text-lg">
            Folha como % da receita, ano a ano
          </h3>
        </div>
        <span className="font-medium text-slate-500 text-xs">
          com os limites da LRF
        </span>
      </div>

      <div className="relative pt-8 pb-4">
        {/* Horizontal Threshold Lines */}
        <div className="absolute inset-x-0 top-8 bottom-12 flex flex-col justify-between pointer-events-none">
          {/* Legal 54% */}
          <div className="relative border-red-400 border-t border-solid w-full">
            <span className="absolute right-0 -top-2.5 font-semibold text-[11px] text-red-600 bg-white px-1">
              legal 54%
            </span>
          </div>

          {/* Prudencial 51.3% */}
          <div className="relative border-orange-400 border-t border-dashed w-full">
            <span className="absolute right-0 -top-2.5 font-semibold text-[11px] text-orange-600 bg-white px-1">
              prudencial 51,3%
            </span>
          </div>

          {/* Alerta 48.6% */}
          <div className="relative border-yellow-500 border-t border-dotted w-full">
            <span className="absolute right-0 -top-2.5 font-semibold text-[11px] text-yellow-700 bg-white px-1">
              alerta 48,6%
            </span>
          </div>
        </div>

        {/* Bars Container */}
        <div className="relative z-10 flex items-end justify-around h-56 pt-6">
          {data.map((item) => {
            const heightPct = Math.min(100, (item.percentualFolha / maxPercent) * 100);
            return (
              <div
                key={item.ano}
                className="flex flex-col items-center group w-16"
              >
                {/* Bar Label */}
                <span className="mb-2 font-bold text-xs text-slate-800">
                  {item.percentualFolha.toFixed(1).replace(".", ",")}%
                </span>

                {/* Bar */}
                <div className="w-12 bg-slate-100 rounded-t-md relative flex items-end h-44">
                  <div
                    className={`w-full rounded-t-md transition-all duration-500 ${
                      item.percentualFolha > 54
                        ? "bg-red-500"
                        : item.percentualFolha > 51.3
                        ? "bg-orange-500"
                        : "bg-sky-600"
                    }`}
                    style={{ height: `${heightPct}%` }}
                  />
                </div>

                {/* Year Label */}
                <span className="mt-3 font-medium text-slate-500 text-xs">
                  {item.ano}
                  {item.isCurrentYear ? "*" : ""}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Export `FolhaLrfHistoryChart` in `packages/ui/src/index.ts`**

- [ ] **Step 3: Test compilation of `@transparencia/ui`**

Run: `pnpm --filter @transparencia/ui build`
Expected: Success with no errors.

- [ ] **Step 4: Commit Task 1**

```bash
git add packages/ui/src/components/charts/folha-lrf-history-chart.tsx packages/ui/src/index.ts
git commit -m "feat(ui): add FolhaLrfHistoryChart component"
```

---

### Task 2: Create `DecimoTerceiroCard` component in `packages/ui`

**Files:**
- Create: `packages/ui/src/components/decimo-terceiro-card.tsx`
- Modify: `packages/ui/src/index.ts`

**Interfaces:**
- Consumes: `{ empenhado: number; pago: number; pctPago: number } | null`
- Produces: `DecimoTerceiroCard` React component.

- [ ] **Step 1: Create `decimo-terceiro-card.tsx`**

```tsx
import React from "react";
import { fmtCompact, fmtPercent } from "../utils/formatters";

interface DecimoTerceiroCardProps {
  empenhado: number;
  pago: number;
  pctPago: number;
}

export function DecimoTerceiroCard({
  empenhado,
  pago,
  pctPago,
}: DecimoTerceiroCardProps) {
  const pctInt = Math.min(100, Math.round(pctPago * 100));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* Card Header */}
      <div className="mb-6 flex items-center justify-between">
        <h3 className="font-bold text-slate-900 text-lg">13º salário</h3>
        <span className="font-bold text-emerald-600 text-xs tracking-wide">
          {pctInt}% quitado
        </span>
      </div>

      {/* Metric Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div>
          <span className="block text-slate-500 text-xs mb-1">
            Total reservado (ajustado)
          </span>
          <span className="font-bold text-slate-900 text-2xl font-serif">
            {fmtCompact(empenhado)}
          </span>
        </div>

        <div>
          <span className="block text-slate-500 text-xs mb-1">
            Efetivamente pago
          </span>
          <span className="font-bold text-slate-900 text-2xl font-serif">
            {fmtCompact(pago)}
          </span>
        </div>

        <div>
          <span className="block text-slate-500 text-xs mb-1">
            Percentual quitado
          </span>
          <span className="font-bold text-emerald-600 text-2xl">
            {pctInt}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden">
        <div
          className="bg-emerald-600 h-full rounded-full transition-all duration-500"
          style={{ width: `${pctInt}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Export `DecimoTerceiroCard` in `packages/ui/src/index.ts`**

- [ ] **Step 3: Test compilation of `@transparencia/ui`**

Run: `pnpm --filter @transparencia/ui build`
Expected: Success with no errors.

- [ ] **Step 4: Commit Task 2**

```bash
git add packages/ui/src/components/decimo-terceiro-card.tsx packages/ui/src/index.ts
git commit -m "feat(ui): add DecimoTerceiroCard component"
```

---

### Task 3: Assemble redesigned Pessoal page in `apps/web`

**Files:**
- Modify: `apps/web/app/[portalSlug]/pessoal/page.tsx`

**Interfaces:**
- Consumes: `getFolhaVsServicos`, `getPercentualChefiasEfetivas`, `getExecucaoDecimoTerceiro` from `@transparencia/db`.
- Produces: Redesigned Next.js server page.

- [ ] **Step 1: Update `apps/web/app/[portalSlug]/pessoal/page.tsx`**

```tsx
import {
  getExecucaoDecimoTerceiro,
  getFolhaVsServicos,
  getPercentualChefiasEfetivas,
} from "@transparencia/db";
import {
  DecimoTerceiroCard,
  FolhaLrfHistoryChart,
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface PessoalPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function PessoalPage({
  params,
  searchParams,
}: PessoalPageProps) {
  const { portalSlug: _portalSlug } = await params;
  const resolvedSearchParams = await searchParams;

  const currentYear = new Date().getFullYear();
  const selectedYear = resolvedSearchParams.ano
    ? Number(resolvedSearchParams.ano)
    : currentYear;
  const entidadesIds = resolvedSearchParams.entidades
    ? resolvedSearchParams.entidades.split(",").filter(Boolean)
    : undefined;

  const isCurrentYear = selectedYear === currentYear;
  const partialPeriod = getPartialYearPeriod();

  // Queries
  const yearsHistory = [
    selectedYear - 4,
    selectedYear - 3,
    selectedYear - 2,
    selectedYear - 1,
    selectedYear,
  ];

  const folhaData = await getFolhaVsServicos(yearsHistory, entidadesIds);
  const pctChefias = await getPercentualChefiasEfetivas(selectedYear, entidadesIds);
  const decimo13 = await getExecucaoDecimoTerceiro(selectedYear, entidadesIds);

  const currentYearRow = folhaData.find((r) => r.ano === selectedYear) || {
    totalFolha: 0,
    totalPago: 0,
    rclProxy: 0,
    percentualFolha: 0,
  };

  const chartItems = folhaData.map((r) => ({
    ano: r.ano,
    percentualFolha: r.percentualFolha,
    isCurrentYear: r.ano === currentYear,
  }));

  return (
    <div className="space-y-8 pb-10">
      {/* Header & Subtitle */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="font-bold font-serif text-3xl text-slate-900">
          Folha de Pagamento
        </h1>
        <p className="mt-2 max-w-4xl text-slate-600 text-xs leading-relaxed sm:text-sm">
          Quanto da receita arrecadada é comprometido com salários e proventos.
          A Lei de Responsabilidade Fiscal limita esse gasto a{" "}
          <strong className="font-semibold text-slate-900">
            54% da receita corrente líquida
          </strong>{" "}
          para o Poder Executivo.
        </p>
      </div>

      {/* 3 Key KPI Cards */}
      <KPIGrid columns={3}>
        <KPICard
          title="Folha / Receita Arrecadada"
          value={fmtPercent(currentYearRow.percentualFolha)}
          subtext={
            currentYearRow.percentualFolha <= 54
              ? "abaixo do teto de 54%"
              : "acima do teto de 54%"
          }
          alert={currentYearRow.percentualFolha > 54}
          accent
        />
        <KPICard
          title="Efetivos no comando das chefias"
          value={pctChefias !== null ? fmtPercent(pctChefias) : "N/D"}
          subtext="cargos de liderança concursados"
        />
        <KPICard
          title="Total pago em folha"
          value={fmtCompact(currentYearRow.totalFolha)}
          subtext={`proventos brutos, ${selectedYear}`}
        />
      </KPIGrid>

      {/* Historical LRF Chart */}
      <FolhaLrfHistoryChart data={chartItems} />

      {/* 13º Salário Card */}
      {decimo13 ? (
        <DecimoTerceiroCard
          empenhado={decimo13.empenhado}
          pago={decimo13.pago}
          pctPago={decimo13.pctPago}
        />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm text-center text-slate-500 text-sm">
          Sem dados de 13º salário para {selectedYear}.
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Run TypeScript / Next build check**

Run: `pnpm --filter @transparencia/web build`
Expected: Build succeeds cleanly.

- [ ] **Step 3: Run project tests**

Run: `make test/ts`
Expected: All tests pass.

- [ ] **Step 4: Commit Task 3**

```bash
git add apps/web/app/[portalSlug]/pessoal/page.tsx
git commit -m "feat(web): update Pessoal page layout to match redesign"
```
