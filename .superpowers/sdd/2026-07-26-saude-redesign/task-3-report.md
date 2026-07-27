# Task 3 Report: Redesign the Web Page `apps/web/app/[portalSlug]/saude/page.tsx`

## Status
- **Result**: DONE
- **Commit**: see git status / log below

## Changes Implemented
1. **Header & Subtitle**:
   - Added category tag `TEMAS · EXERCÍCIO {selectedYear}{isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}`.
   - Title set to `Fundo Municipal de Saúde` with serif typography.
   - Subtitle formatted with bold emphasis on `"o que entrou"`.

2. **Top KPI Grid (`KPIGrid` columns=4)**:
   - Card 1: Dotação Atualizada (`fmtCompact(saude.orcamento.dotacao)`)
   - Card 2: Total Empenhado (`fmtCompact(saude.orcamento.empenhado)` with blue accent text)
   - Card 3: Taxa de Execução (`fmtPercent(saude.orcamento.taxaExecucao * 100)`)
   - Card 4: Medicamentos e Insumos (`fmtCompact(saude.farmaceutica.medicamentosInsumos)`)

3. **Section 1: "O que entrou no Fundo"**:
   - Header with divider line.
   - 2-column layout (Donut chart on left, Repasses and Emendas cards on right).

4. **Section 2: "Empenhado ano a ano"**:
   - Header with divider line.
   - Evolution trend bar chart (`SaudeTrendChart`).

5. **Section 3: "Insumos e assistência farmacêutica"**:
   - Header with divider line.
   - 3-column KPI card grid (Medicamentos e insumos, Judicialização da saúde, Concentração HHI).

6. **Section 4: "Emendas Parlamentares Destinadas à Saúde"**:
   - Header with divider line.
   - Interactive `DenseTable` with search capabilities.

7. **Alert Box**:
   - Warning box rendered when `saude.orcamento.alertaSubExecucao` is true.

## Verification
- Ran `pnpm --filter web build` successfully with zero TypeScript / Next.js compilation errors.
