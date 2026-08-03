# Especificação do Redesign da Página da Saúde

## Visão Geral
Redesign completo da página da Saúde (`apps/web/app/[portalSlug]/saude/page.tsx`) alinhando o layout com os novos padrões visuais do portal de transparência e o protótipo de alta fidelidade fornecido.

---

## 1. Arquitetura e Camada de Dados (`@transparencia/db`)

Toda a inteligência contábil e de consulta pertence ao arquivo `packages/db/src/queries/historia_saude.ts`. A função `getHistoriaSaude` será estendida para retornar uma estrutura de dados unificada e tipada.

### Estritura dos Tipos:
```typescript
export interface BudgetSaude {
  dotacao: number;
  empenhado: number;
  taxaExecucao: number;
  alertaSubExecucao: boolean;
  medicamentosInsumos: number;
}

export interface FontesReceitaSaude {
  uniaoSusPct: number;
  estadoPct: number;
  propriaPct: number;
  repassesPrefeitura: number;
  emendasParlamentares: number;
}

export interface AssistenciaFarmaceuticaSaude {
  medicamentosInsumos: number; // Subfunção 10.303
  judicializacao: number;       // Gastos com sentenças judiciais na saúde
  hhi: number;                  // Índice de Concentração Herfindahl-Hirschman
  hhiClassificacao: string;     // Ex: "moderada a alta"
}

export interface ExecutionTrendSaude {
  ano: number;
  empenhado: number;
}

export interface EmendaSaude {
  Nº: string;
  Objeto: string;
  "Valor Autorizado": number;
  Empenhado: number | null;
  Autor: string;
  "Tipo da Emenda": string;
  "Esfera de Origem": string;
  "Ato Normativo": string;
  Destinação: string;
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

### Consultas SQL e Regras Contábeis:
1. **Filtro por Portal (`portalSlug`)**: Todas as queries na base de dados devem obrigatoriamente respeitar a separação por portal/empresa.
2. **Receita por Fonte**: Consulta de receitas do Fundo Municipal de Saúde categorizadas por Transferências da União (SUS), Transferências do Estado e Receita Própria/Repasses diretos.
3. **Tendência Histórica de Empenho**: Agrupamento dos empenhos do Fundo Municipal de Saúde por ano (ex: 2020 até o exercício atual).
4. **Assistência Farmacêutica & Judicialização**: Consulta dos empenhos por subfunção `10.303` (Assistência Farmacêutica) e elementos/itens de despesa referentes a sentenças/demandas judiciais.
5. **Cálculo de HHI de Saúde**: Medição da concentração dos maiores fornecedores contratados pelo Fundo Municipal de Saúde.

---

## 2. Componentes de Visualização (`@transparencia/ui`)

Novos componentes e reaproveitamento de componentes existentes em `packages/ui/src/components`:

- `KPIGrid` e `KPICard`:
  - Linha superior com 4 cards principais (Dotação Atualizada, Total Empenhado, Taxa de Execução, Medicamentos e Insumos).
  - Linha inferior com 3 cards de Assistência Farmacêutica (Medicamentos e Insumos, Judicialização, Concentração HHI).
- `SaudeFontesDonut` (ou `DonutChart` genérico em Recharts):
  - Gráfico de Rosca exibindo as proporções de receita do Fundo por origem.
- `SaudeExecutionTrendChart` (Gráfico de Barras em Recharts):
  - Exibição visual da evolução anual dos empenhos do Fundo da Saúde.
- `DenseTable`:
  - Exibição e busca interativa das emendas parlamentares destinadas à Saúde.

---

## 3. Estrutura da Página Web (`apps/web/app/[portalSlug]/saude/page.tsx`)

- **Cabeçalho**: Tag de contexto `TEMAS · EXERCÍCIO {ANO} (PARCIAL, {PERÍODO})`, Título `Fundo Municipal de Saúde` em fonte serifada e subtítulo explicativo.
- **Seção 1 - Visão Geral Orçamentária**: 4 KPI Cards.
- **Seção 2 - O que entrou no Fundo**: Donut de Fontes de Receita à esquerda + Cards de Repasses da Prefeitura e Emendas Parlamentares à direita.
- **Seção 3 - Empenhado ano a ano**: Card expansivo contendo o gráfico de barras históricas de 2020 a 2025.
- **Seção 4 - Insumos e assistência farmacêutica**: 3 KPI Cards detalhando subfunção 10.303, demandas judiciais e HHI.
- **Seção 5 - Emendas Parlamentares Destinadas à Saúde**: Tabela `DenseTable` com filtro de busca e paginação.

---

## 4. Garantia de Qualidade e Testes
- Executar `pnpm build` ou `tsc --noEmit` para garantir zero erros de tipagem no TypeScript.
- Executar `make test` e `make test/ts` para assegurar paridade e testes limpos.
