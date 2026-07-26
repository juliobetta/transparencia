# Design Doc: Redesign da Página Pessoal & Vencimentos

**Data:** 2026-07-26  
**Status:** Aprovado  
**Escopo:** Frontend (`apps/web/app/[portalSlug]/pessoal/page.tsx`), Componentes UI (`packages/ui`), Queries DB (`packages/db`).

---

## 1. Visão Geral
Redesign completo da página de Pessoal & Vencimentos para alinhar com o novo padrão visual do Portal da Transparência, trazendo visualização limpa e focada nos limites da Lei de Responsabilidade Fiscal (LRF), representatividade de concursados na liderança, dados históricos de 5 anos e acompanhamento da execução do 13º Salário.

---

## 2. Componentes e Estrutura de Interface

### 2.1 Cabeçalho Padronizado
- **Badge de contexto:** `ADMINISTRATIVO · EXERCÍCIO {selectedYear} (PARCIAL, JAN–AGO)` (usando `getPartialYearPeriod()` quando for o ano corrente).
- **Título principal:** `Folha de Pagamento`
- **Subtítulo:** "Quanto da receita arrecadada é comprometido com salários e proventos. A Lei de Responsabilidade Fiscal limita esse gasto a **54% da receita corrente líquida** para o Poder Executivo."

### 2.2 Cards de KPI Principais (Grid 3 Colunas)
Utilizando `KPIGrid` e `KPICard` de `@transparencia/ui`:
1. **Folha / Receita Arrecadada**
   - Valor: `%` do comprometimento da folha vs RCL (`percentualFolha`).
   - Subtexto: `abaixo do teto de 54%` (verde se $\le 54\%$) ou `acima do teto de 54%` (vermelho/alerta se $> 54\%$).
2. **Efetivos no comando das chefias**
   - Valor: `%` de lideranças exercidas por servidores concursados/efetivos (`pctChefias`).
   - Subtexto: `cargos de liderança concursados`.
3. **Total pago em folha**
   - Valor: Valor formatado em moeda (`totalFolha`).
   - Subtexto: `proventos brutos, {selectedYear}`.

### 2.3 Gráfico Histórico: "Folha como % da receita, ano a ano"
- **Componente:** `FolhaLrfHistoryChart` em `packages/ui/src/components/charts/folha-lrf-history-chart.tsx`.
- **Dados:** Histórico de 5 anos (de `selectedYear - 4` até `selectedYear`) retornado por `getFolhaVsServicos`.
- **Linhas de Referência da LRF:**
  - **Teto Legal:** 54,0% (Linha sólida vermelha `#DC2626`)
  - **Limite Prudencial:** 51,3% (Linha tracejada laranja `#EA580C`)
  - **Limite de Alerta:** 48,6% (Linha pontilhada amarela/dourada `#CA8A04`)
- **Rótulos:** Exibição do valor em `%` acima de cada barra do ano (ex: `48,2%*` para o ano parcial).

### 2.4 Seção: "13º salário"
- **Componente:** `DecimoTerceiroCard` em `packages/ui/src/components/decimo-terceiro-card.tsx`.
- **Cabeçalho da Seção:** Título `13º salário` com badge de status alinhado à direita (ex: `100% quitado`).
- **Métricas:**
  - `Total reservado (ajustado)` (Empenhado líquido / ajustado).
  - `Efetivamente pago` (Valor pago).
  - `Percentual quitado` (`pctPago * 100`).
- **Barra de Progresso:** Barra horizontal em tom de verde preenchendo a porcentagem quitada.

---

## 3. Camada de Dados (`@transparencia/db`)
- Reutilização e integração das queries existentes em `packages/db/src/queries/folha_vs_servicos.ts`:
  - `getFolhaVsServicos(years)`
  - `getPercentualChefiasEfetivas(year)`
  - `getExecucaoDecimoTerceiro(year)`

---

## 4. Estratégia de Testes e Validação
- **Tipagem:** Verificar compilação TypeScript sem erros (`pnpm build` ou `tsc --noEmit`).
- **Testes:** Executar suíte de testes (`make test/ts`).
