# Design Doc: Redesign da Página Pessoal & Vencimentos (v2)

**Data:** 2026-07-26  
**Status:** Aprovado  
**Escopo:** Frontend (`apps/web/app/[portalSlug]/pessoal/page.tsx`), Componentes UI (`packages/ui`), Queries DB (`packages/db`).

---

## 1. Visão Geral
Redesign completo da página de Pessoal & Vencimentos alinhado ao padrão visual do Portal da Transparência, integrando:
1. Histograma de **Distribuição dos Proventos Brutos** (faixas salariais dos servidores).
2. Análise de **Pagamentos via Responsáveis de Secretaria** (pagamentos agrupados com sufixo `E OUTROS`).
3. Diagnóstico ajustado do **13º Salário** (verificando a abrangência da query para anos anteriores).
4. Indicadores de topo (Comprometimento LRF, Cargos de Chefia Concursados, Proventos Brutos Totais).

---

## 2. Componentes e Estrutura de Interface

### 2.1 Cabeçalho Padronizado
- **Badge de contexto:** `ADMINISTRATIVO · EXERCÍCIO {selectedYear} (PARCIAL, JAN–AGO)` (usando `getPartialYearPeriod()`).
- **Título principal:** `Folha de Pagamento`
- **Subtítulo:** "Quanto da receita arrecadada é comprometido com salários e proventos. A Lei de Responsabilidade Fiscal limita esse gasto a **54% da receita corrente líquida** para o Poder Executivo."

### 2.2 Cards de KPI Principais (Grid 3 Colunas)
1. **Folha / Receita Arrecadada**: `%` do comprometimento da folha vs RCL (`percentualFolha`).
2. **Efetivos no comando das chefias**: `%` de concursados/efetivos em cargos de liderança (`pctChefias`).
3. **Total pago em folha**: Proventos brutos acumulados no ano (`totalFolha`).

### 2.3 Seção 1: "Distribuição dos Proventos Brutos"
- **Componente:** `ProventosDistributionChart` em `packages/ui/src/components/charts/proventos-distribution-chart.tsx`.
- **Descrição:** Gráfico de histograma indicando o número de servidores por faixa de proventos (R$ 0 a R$ 20.000+).
- **Dados:** Provindo da query `getDistribuicaoProventos(year)` em `@transparencia/db`.

### 2.4 Seção 2: "Pagamentos via Responsáveis de Secretaria"
- **Componente:** `DepartmentalPayrollChart` em `packages/ui/src/components/charts/departmental-payroll-chart.tsx`.
- **Card Informativo:** Explicativo sobre a prática de empenho da folha no CPF do ordenador da unidade (sufixo `E OUTROS`).
- **Gráfico:** Barras horizontais com total pago por responsável.
- **Dados:** Provindo da query `getDepartmentalPayroll(year)` em `@transparencia/db`.

### 2.5 Seção 3: "13º salário"
- **Componente:** `DecimoTerceiroCard` em `packages/ui/src/components/decimo-terceiro-card.tsx`.
- **Métricas:** Total reservado (ajustado), Efetivamente pago, Percentual quitado.
- **Barra de Progresso:** Barra verde horizontal.
- **Query de Banco:** Ajustar `getExecucaoDecimoTerceiro` para garantir captura correta nos anos anteriores (removendo filtros de elemento restritivos).

---

## 3. Camada de Dados (`@transparencia/db`)
- `getDistribuicaoProventos(year: number)`
- `getDepartmentalPayroll(year: number, empresaIds?: string[])`
- Ajuste em `getExecucaoDecimoTerceiro(year: number, empresaIds?: string[])`
