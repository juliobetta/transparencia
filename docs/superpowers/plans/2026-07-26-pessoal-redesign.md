# Redesign da Página Pessoal Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete redesign of the Pessoal & Vencimentos page featuring 3 key KPI cards, Salary Distribution histogram chart, Departmental Payroll bar chart with explanation info box, and fixed 13º Salário execution tracking across prior years.

**Architecture:** Create DB queries in `@transparencia/db`, build `ProventosDistributionChart` and `DepartmentalPayrollChart` UI components in `packages/ui`, and assemble `apps/web/app/[portalSlug]/pessoal/page.tsx`.

**Tech Stack:** Next.js (App Router), React, Tailwind CSS, TypeScript, `@transparencia/db`, `@transparencia/ui`.

## Global Constraints
- Strictly follow DRY architecture (`@transparencia/db` for queries, `@transparencia/ui` for presentation).
- Visual design must match portal standards (`text-accent`, `font-serif`, `text-slate-900`, `bg-white`, `border-slate-200`, `shadow-sm`).
- Zero build or type errors (`pnpm build` / `make test/ts`).

---

### Task 1: Fix 13º Salário query and add Proventos & Departmental Payroll queries in `@transparencia/db`

**Files:**
- Modify: `packages/db/src/queries/folha_vs_servicos.ts`
- Modify: `packages/db/src/index.ts`

**Interfaces:**
- Produces:
  - `getExecucaoDecimoTerceiro(year: number, empresaIds?: string[])` (fixed to catch 13th salary across prior years)
  - `getDistribuicaoProventos(year: number)` -> `Promise<{ faixa: string; min: number; max: number; count: number }[]>`
  - `getDepartmentalPayroll(year: number, empresaIds?: string[])` -> `Promise<{ descricao: string; pago: number }[]>`

- [ ] **Step 1: Fix `getExecucaoDecimoTerceiro` in `packages/db/src/queries/folha_vs_servicos.ts`**

Broaden search clause in `fct_despesas` to match 13th salary across all elements and subelements:
```ts
export async function getExecucaoDecimoTerceiro(
  year: number,
  empresaIds?: string[] | null,
): Promise<DecimoTerceiroExecucao | null> {
  try {
    let q = sql`
      SELECT
        SUM(CAST(REPLACE(empenhado, ',', '.') AS numeric)) as empenhado_bruto,
        SUM(CAST(REPLACE(empenhado_liquido, ',', '.') AS numeric)) as empenhado_liquido,
        SUM(CAST(REPLACE(liquidado, ',', '.') AS numeric)) as liquidado,
        SUM(CAST(REPLACE(pago, ',', '.') AS numeric)) as pago
      FROM fct_despesas
      WHERE ano = ${year}
        AND (
          descricao ILIKE '%13%' OR
          descricao ILIKE '%decimo terceiro%' OR
          descricao ILIKE '%décimo terceiro%' OR
          historico ILIKE '%13%' OR
          historico ILIKE '%decimo terceiro%' OR
          historico ILIKE '%décimo terceiro%'
        )
        AND descricao NOT ILIKE '%anula%'
        AND descricao NOT ILIKE '%136%'
        AND descricao NOT ILIKE '%137%'
        AND descricao NOT ILIKE '%138%'
        AND descricao NOT ILIKE '%139%'
        AND tipo_empenho != 'AN'
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa_id = ANY(${empresaIds})`;
    }
    const res = await q.execute(db);

    const r = (res.rows as any[])?.[0];
    if (!r || r.empenhado_bruto === null || r.empenhado_bruto === undefined)
      return null;

    const empBruto = parseFloat(String(r.empenhado_bruto ?? "0")) || 0;
    const empLiq = parseFloat(String(r.empenhado_liquido ?? "0")) || empBruto;
    const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
    const pag = parseFloat(String(r.pago ?? "0")) || 0;
    const pctPago = empLiq > 0 ? pag / empLiq : 0;

    return {
      empenhado: empLiq,
      empenhadoBruto: empBruto,
      liquidado: liq,
      pago: pag,
      pctPago,
    };
  } catch {
    return null;
  }
}
```

- [ ] **Step 2: Add `getDistribuicaoProventos` & `getDepartmentalPayroll` in `folha_vs_servicos.ts`**

```ts
export interface SalaryBin {
  faixa: string;
  min: number;
  max: number;
  count: number;
}

export async function getDistribuicaoProventos(year: number): Promise<SalaryBin[]> {
  try {
    const res = await sql`
      SELECT proventos
      FROM fct_pessoal
      WHERE ano = ${year}
    `.execute(db);

    const values: number[] = [];
    for (const r of (res.rows as any[]) || []) {
      const v = parseFloat(String(r.proventos ?? "0").replace(",", "."));
      if (!Number.isNaN(v) && v > 0) {
        values.push(v);
      }
    }

    const BINS = [
      { faixa: "R$ 0 - 2,5k", min: 0, max: 2500 },
      { faixa: "R$ 2,5k - 5k", min: 2500, max: 5000 },
      { faixa: "R$ 5k - 7,5k", min: 5000, max: 7500 },
      { faixa: "R$ 7,5k - 10k", min: 7500, max: 10000 },
      { faixa: "R$ 10k - 12,5k", min: 10000, max: 12500 },
      { faixa: "R$ 12,5k - 15k", min: 12500, max: 15000 },
      { faixa: "R$ 15k - 17,5k", min: 15000, max: 17500 },
      { faixa: "R$ 17,5k - 20k", min: 17500, max: 20000 },
      { faixa: "> R$ 20k", min: 20000, max: Infinity },
    ];

    const counts = BINS.map((b) => ({ ...b, count: 0 }));
    for (const val of values) {
      for (const b of counts) {
        if (val >= b.min && (val < b.max || b.max === Infinity)) {
          b.count += 1;
          break;
        }
      }
    }

    return counts;
  } catch {
    return [];
  }
}

export interface DepartmentalPayrollItem {
  descricao: string;
  pago: number;
}

export async function getDepartmentalPayroll(
  year: number,
  empresaIds?: string[] | null,
): Promise<DepartmentalPayrollItem[]> {
  try {
    let q = sql`
      SELECT
        descricao,
        SUM(CAST(REPLACE(pago, ',', '.') AS numeric)) as total_pago
      FROM fct_despesas_por_fornecedor
      WHERE ano = ${year}
        AND (descricao ~* ' E OUT(ROS?|\\.)' OR descricao ILIKE '%E OUTROS%' OR descricao ILIKE '%E OUTRO%')
    `;
    if (empresaIds && empresaIds.length > 0) {
      q = sql`${q} AND empresa = ANY(${empresaIds})`;
    }
    q = sql`${q} GROUP BY descricao ORDER BY total_pago DESC`;

    const res = await q.execute(db);
    return (res.rows as any[]).map((r) => ({
      descricao: String(r.descricao || ""),
      pago: parseFloat(String(r.total_pago ?? "0")) || 0,
    }));
  } catch {
    return [];
  }
}
```

- [ ] **Step 3: Export queries in `packages/db/src/index.ts`**

- [ ] **Step 4: Verify build & tests**

Run: `make test/ts`
Expected: Passes clean with 0 errors.

- [ ] **Step 5: Commit Task 1**

```bash
git add packages/db/src/queries/folha_vs_servicos.ts packages/db/src/index.ts
git commit -m "feat(db): update 13th salary query and add proventos distribution and departmental payroll queries"
```

---

### Task 2: Create `ProventosDistributionChart` component in `packages/ui`

**Files:**
- Create: `packages/ui/src/components/charts/proventos-distribution-chart.tsx`
- Modify: `packages/ui/src/index.ts`

**Interfaces:**
- Consumes: `{ faixa: string; min: number; max: number; count: number }[]`
- Produces: `ProventosDistributionChart` React component.

- [ ] **Step 1: Create `proventos-distribution-chart.tsx`**

```tsx
import React from "react";

export interface SalaryBinItem {
  faixa: string;
  min: number;
  max: number;
  count: number;
}

interface ProventosDistributionChartProps {
  data: SalaryBinItem[];
}

export function ProventosDistributionChart({
  data,
}: ProventosDistributionChartProps) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4">
        <h3 className="font-bold text-slate-900 text-lg">
          Distribuição dos Proventos Brutos
        </h3>
        <p className="mt-1 text-slate-500 text-xs">
          O portal não disponibiliza a remuneração líquida individual. O gráfico
          abaixo utiliza os proventos (remuneração bruta) como aproximação.
        </p>
      </div>

      <div className="relative pt-6 pb-2">
        <div className="flex items-end justify-between h-56 gap-2 pt-6 px-2">
          {data.map((item) => {
            const heightPct = Math.min(100, (item.count / maxCount) * 100);
            return (
              <div
                key={item.faixa}
                className="flex flex-col items-center flex-1 group"
              >
                {/* Count Label */}
                <span className="mb-1 font-bold text-xs text-slate-700">
                  {item.count}
                </span>

                {/* Bar Container */}
                <div className="w-full bg-slate-100 rounded-t-sm relative flex items-end h-44">
                  <div
                    className="w-full bg-sky-600 rounded-t-sm transition-all duration-500 group-hover:bg-sky-700"
                    style={{ height: `${heightPct}%` }}
                    title={`${item.faixa}: ${item.count} servidores`}
                  />
                </div>

                {/* Range Label */}
                <span className="mt-2 text-[10px] text-slate-500 font-medium text-center truncate max-w-full">
                  {item.faixa}
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

- [ ] **Step 2: Export in `packages/ui/src/index.ts`**

- [ ] **Step 3: Test compilation**

Run: `pnpm --filter @transparencia/ui build`
Expected: Success.

- [ ] **Step 4: Commit Task 2**

```bash
git add packages/ui/src/components/charts/proventos-distribution-chart.tsx packages/ui/src/index.ts
git commit -m "feat(ui): add ProventosDistributionChart component"
```

---

### Task 3: Create `DepartmentalPayrollChart` component in `packages/ui`

**Files:**
- Create: `packages/ui/src/components/charts/departmental-payroll-chart.tsx`
- Modify: `packages/ui/src/index.ts`

**Interfaces:**
- Consumes: `{ descricao: string; pago: number }[]` and `selectedYear: number`.
- Produces: `DepartmentalPayrollChart` React component.

- [ ] **Step 1: Create `departmental-payroll-chart.tsx`**

```tsx
import React from "react";
import { fmtCompact } from "../../utils/formatters";

export interface DepartmentalItem {
  descricao: string;
  pago: number;
}

interface DepartmentalPayrollChartProps {
  data: DepartmentalItem[];
  selectedYear: number;
}

export function DepartmentalPayrollChart({
  data,
  selectedYear,
}: DepartmentalPayrollChartProps) {
  const maxPaid = Math.max(...data.map((d) => d.pago), 1);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="font-bold font-serif text-xl text-slate-900">
          Pagamentos via Responsáveis de Secretaria
        </h2>
      </div>

      {/* Info Callout Box */}
      <div className="rounded-xl border border-sky-200 bg-sky-50/60 p-5 text-sky-900">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-sky-600 font-bold text-base">ℹ</div>
          <div className="space-y-2 text-xs leading-relaxed">
            <h4 className="font-semibold text-slate-900 text-sm">
              Por que uma pessoa aparece recebendo milhões de reais?
            </h4>
            <p className="text-slate-700">
              No Brasil, é prática comum em municípios que o ordenador de
              despesas de cada secretaria (o responsável pelo departamento)
              receba o montante total da folha de pagamento em seu CPF e o
              distribua entre os servidores da unidade. O sufixo{" "}
              <strong className="font-semibold text-slate-900">
                &quot;E OUTROS&quot;
              </strong>{" "}
              no nome indica exatamente isso: o valor não é de uso pessoal —
              representa salários de toda a equipe.
            </p>
            <p className="text-slate-600 font-medium">
              Esses pagamentos são excluídos da análise de Fornecedores e Compras
              Locais para não distorcer os índices de concentração e compras
              locais.
            </p>
          </div>
        </div>
      </div>

      {/* Bar Chart Container */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold text-slate-900 text-base mb-6">
          Folha distribuída por responsável ({selectedYear})
        </h3>

        {data.length === 0 ? (
          <p className="text-slate-500 text-sm text-center py-6">
            Nenhum pagamento registrado nesta categoria para este exercício.
          </p>
        ) : (
          <div className="space-y-4">
            {data.map((item) => {
              const widthPct = Math.min(100, (item.pago / maxPaid) * 100);
              return (
                <div key={item.descricao} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-800 truncate max-w-xl">
                      {item.descricao}
                    </span>
                    <span className="font-bold text-slate-900 ml-2">
                      {fmtCompact(item.pago)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-3 rounded-md overflow-hidden">
                    <div
                      className="bg-sky-600 h-full rounded-md transition-all duration-500"
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Export in `packages/ui/src/index.ts`**

- [ ] **Step 3: Test compilation**

Run: `pnpm --filter @transparencia/ui build`
Expected: Success.

- [ ] **Step 4: Commit Task 3**

```bash
git add packages/ui/src/components/charts/departmental-payroll-chart.tsx packages/ui/src/index.ts
git commit -m "feat(ui): add DepartmentalPayrollChart component"
```

---

### Task 4: Update Pessoal page layout in `apps/web`

**Files:**
- Modify: `apps/web/app/[portalSlug]/pessoal/page.tsx`

- [ ] **Step 1: Update `page.tsx` with all components and queries**

```tsx
import {
  getDepartmentalPayroll,
  getDistribuicaoProventos,
  getExecucaoDecimoTerceiro,
  getFolhaVsServicos,
  getPercentualChefiasEfetivas,
} from "@transparencia/db";
import {
  DecimoTerceiroCard,
  DepartmentalPayrollChart,
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
  ProventosDistributionChart,
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
  const folhaData = await getFolhaVsServicos([selectedYear], entidadesIds);
  const pctChefias = await getPercentualChefiasEfetivas(selectedYear, entidadesIds);
  const decimo13 = await getExecucaoDecimoTerceiro(selectedYear, entidadesIds);
  const distribuicaoProventos = await getDistribuicaoProventos(selectedYear);
  const departmentalPayroll = await getDepartmentalPayroll(selectedYear, entidadesIds);

  const currentYearRow = folhaData[0] || {
    totalFolha: 0,
    totalPago: 0,
    rclProxy: 0,
    percentualFolha: 0,
  };

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

      {/* Proventos Distribution Histogram Chart */}
      <ProventosDistributionChart data={distribuicaoProventos} />

      {/* Departmental Payroll (E OUTROS) Chart */}
      <DepartmentalPayrollChart
        data={departmentalPayroll}
        selectedYear={selectedYear}
      />

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

- [ ] **Step 2: Run build and typecheck**

Run: `pnpm --filter web build` and `make test/ts`
Expected: Build and tests pass cleanly.

- [ ] **Step 3: Commit Task 4**

```bash
git add apps/web/app/[portalSlug]/pessoal/page.tsx
git commit -m "feat(web): update Pessoal page with salary distribution and departmental payroll charts"
```
