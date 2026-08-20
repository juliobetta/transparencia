---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-transparencia-2026-08-01/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-transparencia-2026-08-01/ARCHITECTURE-SPINE.md
---

# transparencia - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for transparencia, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

- **FR1 (FR-1.1)**: O dbt deve fornecer o modelo `fct_posicao_fiscal_metricas.sql` pré-calculando total arrecadado, despesas pagas, restos pagos e pendentes (separados por gestão anterior vs. atual com auxílio do ano de referência em `dim_metadata`).
- **FR2 (FR-1.2)**: O dbt deve fornecer o modelo `fct_analise_despesas_metricas.sql` pré-agregando totais empenhados, liquidados e pagos por órgãos, unidades e funções contábeis.
- **FR3 (FR-1.3)**: O dbt deve fornecer os modelos `fct_execucao_orcamentaria_metricas.sql`, `fct_fontes_receita_metricas.sql`, `fct_historia_caprem_metricas.sql` e `fct_historia_saude_metricas.sql`, suportados por tabelas dimensionais canônicas padronizadas conforme normas oficiais (STN/MCASP).
- **FR4 (FR-1.4)**: Todos os modelos de métricas e dimensões devem incluir a dimensão `portal_slug` em seu agrupamento obrigatório quando aplicável a multi-tenant.
- **FR5 (FR-2.1)**: A camada `@transparencia/db` deve substituir scripts monolíticos de montagem de telas por leitores burros atômicos (ex: `getPosicaoFiscalMetrics(portalSlug, ano)`, `getHistoriaCapremMetrics(portalSlug, ano)`).
- **FR6 (FR-2.2)**: Nenhuma função em `@transparencia/db` pode conter chamadas a `sql` com agregações `SUM()`, `AVG()` ou `GROUP BY` sobre dados transacionais brutos ou casts e mapeamentos hardcoded em runtime.
- **FR7 (FR-2.3)**: Todas as funções leitoras devem exigir obrigatoriamente o parâmetro `portalSlug`.
- **FR8 (FR-3.1)**: Mover componentes de domínio de `packages/ui/src/components/` para `apps/web/components/` (ex: `caprem-hero-section.tsx`, `saude-emendas-section.tsx`, `posicao-fiscal-hero.tsx`).
- **FR9 (FR-3.2)**: Manter em `packages/ui` apenas primitivas agnósticas de design system (ex: `button.tsx`, `card.tsx`, `dense-table.tsx`, `kpi-card.tsx`).
- **FR10 (FR-4.1)**: Os data loaders e a composição de View Models devem residir em `apps/web/app/` (próximo às rotas que renderizam as telas, como `apps/web/app/[portalSlug]/caprem/page.tsx`).
- **FR11 (FR-4.2)**: Os componentes UI devem receber apenas DTOs prontos passados via props.

### NonFunctional Requirements

- **NFR1 (NFR-1.1)**: Desempenho e Latência: Leituras das páginas principais (ex: Posição Fiscal, CAPREM, Saúde) na web devem responder em menos de 100ms no banco de dados PostgreSQL devido à pré-materialização física (`materialized='table'`).
- **NFR2 (NFR-2.1)**: Integridade e Tolerância Zero a Erros: Testes fiscais e balanços contábeis (ex: `empenhado >= liquidado >= pago`, adimplência atuarial CAPREM) devem falhar a compilação do dbt caso haja discrepância nos dados.
- **NFR3 (NFR-3.1)**: Manutencibilidade e Testabilidade: Mudanças em schemas de staging exigem atualização em `_sources.yml` para garantir que os testes de integração (`make test`) passem sem erro.
- **NFR4 (NFR-3.2)**: Manutencibilidade e Testabilidade: Testes TypeScript (`make test/ts`) devem validar que todas as queries Kysely mantêm tipagem forte e passam o filtro `portal_slug`.
- **NFR5 (Preservação Visual)**: Nenhuma visualização ou tela existente deve ser removida durante a refatoração. A aplicação web deve manter total paridade visual e comportamental com a versão existente para facilitar a migração.
- **NFR6 (Conformidade STN/MCASP)**: A classificação orçamentária de elementos de despesa, naturezas, funções e subfunções deve seguir rigorosamente as tabelas e normas oficiais da Secretaria do Tesouro Nacional (STN) e Manual de Contabilidade Aplicada ao Setor Público (MCASP).

### Additional Requirements

- **AD-1**: dbt Marts de Métricas em `elt/transform/models/marts/metrics/` como Única Fonte da Verdade Contábil (SSOT).
- **AD-2**: Todos os modelos em `elt/transform/models/marts/metrics/` devem ser configurados com `materialized='table'` no dbt.
- **AD-3**: O pacote `@transparencia/db` conterá apenas funções leitoras atômicas e genéricas ("pass-through") que espelham diretamente as tabelas/marts do dbt (`selectFrom('fct_..._metricas').where('portal_slug', '=', portalSlug)`).
- **AD-4**: `packages/ui` restrito a primitivas genéricas e componentes de domínio em `apps/web/components/`. Co-localização de data loaders em `apps/web/app/`.
- **AD-5**: Isolamento Multi-tenant Obrigatório via `portal_slug` em dbt (`GROUP BY portal_slug`) e Kysely.
- **AD-6**: Protocolo de Validação Fiscais em dbt (`dbt test`) e aprovação estrita de `make test` (Python/dbt) e `make test/ts` (TypeScript/Kysely).
- **ASSUMPTION-1**: Projeções Enxutas de Métricas em `marts/metrics/` omitindo campos de texto longo como histórico de empenhos.
- **ASSUMPTION-2**: Referência de Gestão em `dim_metadata` (`ano_inicio_gestao_atual`) para cálculo de restos a pagar anterior vs. atual.
- **ASSUMPTION-3**: Estrutura Plana de Componentes em `apps/web/components/` com nomes descritivos com hífens.

### UX Design Requirements

*Nenhum documento de especificação UX dedicado encontrado. Os requisitos de UI são derivados diretamente dos requisitos FR8-FR11, AD-4 e NFR5 (reorganização da UI, separação de primitivas e componentes de domínio, garantindo 100% de preservação da paridade visual das telas existentes).*

### FR Coverage Map

- **FR1 (FR-1.1)**: Epic 1 - Modelo `fct_posicao_fiscal_metricas.sql` pré-calculando saldos e restos a pagar por gestão.
- **FR2 (FR-1.2)**: Epic 1 - Modelo `fct_analise_despesas_metricas.sql` pré-agregando totais por órgãos, unidades e funções.
- **FR3 (FR-1.3)**: Epic 1 - Auditoria de queries legadas, dimensões canônicas STN/MCASP (`dim_elemento_despesa`, `dim_natureza_despesa`, `dim_funcao_subfuncao`) e modelos `fct_execucao_orcamentaria_metricas.sql`, `fct_fontes_receita_metricas.sql`, `fct_historia_caprem_metricas.sql` e `fct_historia_saude_metricas.sql`.
- **FR4 (FR-1.4)**: Epic 1 - Inclusão da dimensão `portal_slug` em todos os agrupamentos dbt.
- **FR5 (FR-2.1)**: Epic 2 - Substituição de queries monolíticas por leitores burros atômicos em `@transparencia/db`.
- **FR6 (FR-2.2)**: Epic 2 - Eliminação de `SUM()`, `AVG()`, `GROUP BY`, `CAST` e dicionários JS hardcoded em runtime no Kysely.
- **FR7 (FR-2.3)**: Epic 2 - Filtro obrigatório de `portalSlug` em todas as funções leitoras.
- **FR8 (FR-3.1)**: Epic 3 - Migração dos componentes de domínio de `packages/ui` para `apps/web/components/`.
- **FR9 (FR-3.2)**: Epic 3 - Manutenção exclusiva de primitivas agnósticas no `packages/ui`.
- **FR10 (FR-4.1)**: Epic 3 - Co-localização de Data Loaders e composição de View Models em `apps/web/app/`.
- **FR11 (FR-4.2)**: Epic 3 - Transmissão de DTOs puros via props para componentes de UI.

## Epic List

- [Epic 1: Descoberta de Domínios, Dimensões Canônicas (STN/MCASP) e SSOT no dbt](#epic-1-descoberta-de-domínios-dimensões-canônicas-stnmcasp-e-ssot-no-dbt)
- [Epic 2: Leitores Atômicos e Contratos de Dados no `@transparencia/db`](#epic-2-leitores-atômicos-e-contratos-de-dados-no-transparenciadb)
- [Epic 3: Reorganização da UI e Co-localização de Loaders no `apps/web`](#epic-3-reorganização-da-ui-e-co-localização-de-loaders-no-appsweb)
- [Epic 4: Experiência Visual, Responsividade Mobile, SEO & Otimização para LLMs](#epic-4-experiência-visual-responsividade-mobile-seo--otimização-para-llms)

---

## Epic 1: Descoberta de Domínios, Dimensões Canônicas (STN/MCASP) e SSOT no dbt

Realizar o inventário e auditoria de todas as queries TypeScript legadas para extrair regras contábeis ocultas, criar as tabelas de dimensões canônicas oficiais do setor público (`dim_elemento_despesa`, `dim_natureza_despesa`, `dim_funcao_subfuncao`) baseadas nas normas da Secretaria do Tesouro Nacional (STN/MCASP) e consolidar os marts de métricas no dbt materializados fisicamente (`materialized='table'`).

### Story 1.1: Fase de Descoberta e Auditoria de Regras Fiscais Ocultas no TypeScript

As a data/fiscal architect,
I want to audit all legacy TypeScript queries in `@transparencia/db/src/queries/` to catalog all domain-specific filters, element mappings, and hardcoded constants,
So that no domain logic or accounting rule is lost during the migration to dbt.

**Acceptance Criteria:**

**Given** as funções leitoras legadas em `@transparencia/db/src/queries/` (ex: `historia_caprem.ts`, `historia_saude.ts`, `posicao_fiscal.ts`, `despesas.ts`)
**When** a auditoria de regras contábeis e de-para ocultos for realizada
**Then** é gerado um inventário mapeando todas as constantes hardcoded (ex: `CAPREM_CODE`, `CASP_CNPJ`, códigos de elemento `13`, `46`, `71`, `91`, `97`), joins com credores específicos e fórmulas de cálculo atuarial/saúde.
**And** cada item do inventário é associado à especificação correspondente nas tabelas oficiais do STN/MCASP.

### Story 1.2: Modelagem das Dimensões Canônicas Fiscais (STN/MCASP) no dbt

As a data engineer,
I want canonical dimension tables for expense elements, nature of expense, functions, and subfunctions built in dbt according to official STN/MCASP standards,
So that all metrics models join against standardized official classifications rather than using hardcoded JavaScript dictionaries.

**Acceptance Criteria:**

**Given** a especificação oficial de classificação orçamentária da Portaria STN/SOF nº 163/2001 e Portaria STN nº 448/2002 (MCASP)
**When** as dimensões `dim_elemento_despesa.sql`, `dim_natureza_despesa.sql` e `dim_funcao_subfuncao.sql` são criadas no dbt
**Then** elas contêm o catálogo completo e oficial de elementos de despesa, especificações, descrições e títulos contábeis regulamentados.
**And** o de-para legado (ex: `ELEMENTO_LABELS`) é totalmente substituído pelo `JOIN` nativo com `dim_elemento_despesa`.
**And** a suíte `make test` executa e valida as novas dimensões no banco de testes efêmero.

### Story 1.3: Modelo de Métricas de Posição Fiscal no dbt (`fct_posicao_fiscal_metricas`)

As a fiscal analyst / system,
I want pre-calculated financial metrics for daily and annual fiscal positioning in a materialized dbt table,
So that screen queries do not calculate totals from raw transactional data at runtime.

**Acceptance Criteria:**

**Given** as tabelas raw de receita e despesa sincronizadas em `_sources.yml` e o schema efêmero configurado
**When** o comando `dbt run --select fct_posicao_fiscal_metricas` é executado
**Then** a tabela física `fct_posicao_fiscal_metricas` é criada em `elt/transform/models/marts/metrics/` com materialização `table` contendo as colunas `portal_slug`, `ano`, `total_arrecadado`, `despesas_pagas`, `restos_pagos_no_ano`, `restos_pendentes_adm_anterior`, `restos_pendentes_adm_atual` e `saldo_estimado`.
**And** os restos a pagar são corretamente segregados entre gestão anterior e atual utilizando a referência em `dim_metadata`.
**And** a dimensão `portal_slug` é obrigatoriamente incluída no agrupamento do modelo.
**And** os testes do dbt (`total_arrecadado >= 0`) e a suíte `make test` executam e passam com 100% de sucesso.

### Story 1.4: Modelo de Métricas de Análise de Despesas no dbt (`fct_analise_despesas_metricas`)

As a fiscal analyst / system,
I want pre-aggregated totals for empenhado, liquidado, and pago grouped by portal_slug, ano, orgao, unidade, and funcao,
So that expense breakdowns load instantly with strict accounting consistency.

**Acceptance Criteria:**

**Given** as tabelas de staging de empenhos, liquidações e pagamentos
**When** o modelo `fct_analise_despesas_metricas` é executado no dbt
**Then** a tabela física `fct_analise_despesas_metricas` é criada com `materialized='table'` contendo agrupamento por `portal_slug`, `ano`, `orgao_codigo`, `unidade_codigo` e `funcao_codigo`.
**And** o modelo pré-calcula os somatórios de `total_empenhado`, `total_liquidado` e `total_pago`.
**And** o teste fiscal de invariante contábil (`total_empenhado >= total_liquidado AND total_liquidado >= total_pago`) é declarado em `schema.yml` e validado via `dbt test`.
**And** a suíte de testes `make test` é aprovada sem erros.

### Story 1.5: Modelos de Métricas de Domínio Específico no dbt (`fct_execucao_orcamentaria_metricas`, `fct_fontes_receita_metricas`, `fct_historia_caprem_metricas` e `fct_historia_saude_metricas`)

As a fiscal analyst / system,
I want pre-aggregated budgetary execution, revenue sources, CAPREM actuarial metrics, and Health story metrics models in dbt using official dimension tables,
So that domain-specific cross-referencing, casts, and complex filtering happen at data materialization time without runtime overhead.

**Acceptance Criteria:**

**Given** as tabelas raw de empenhos, folhas de pagamento, credores e as dimensões `dim_elemento_despesa`, `dim_natureza_despesa`, `dim_funcao_subfuncao`
**When** os modelos `fct_execucao_orcamentaria_metricas`, `fct_fontes_receita_metricas`, `fct_historia_caprem_metricas` e `fct_historia_saude_metricas` são executados no dbt
**Then** todas as tabelas são materializadas fisicamente (`materialized='table'`) em `elt/transform/models/marts/metrics/` contendo a dimensão obrigatória `portal_slug`.
**And** `fct_historia_caprem_metricas` utiliza as tabelas de dimensões oficiais para cruzamentos de empenhos patronais/aportes e indicadores atuariais.
**And** `fct_historia_saude_metricas` consolida os indicadores de aplicação da saúde.
**And** os testes de schema dbt e `make test` são aprovados com sucesso.

---

## Epic 2: Leitores Atômicos e Contratos de Dados no `@transparencia/db`

Refatorar a biblioteca de acesso a dados `@transparencia/db` para agir estritamente como um leitor burro "pass-through" fortemente tipado via Kysely, eliminando todas as agregações runtime em TypeScript e impondo a filtragem por `portalSlug`.

### Story 2.1: Leitores Burros Atômicos para Posição Fiscal (`getPosicaoFiscalMetrics`)

As a developer,
I want an atomic Kysely reader function for Posição Fiscal metrics in `@transparencia/db`,
So that server components receive strongly typed DTOs directly from pre-materialized dbt marts without runtime SQL aggregations.

**Acceptance Criteria:**

**Given** a tabela materializada `fct_posicao_fiscal_metricas` no banco PostgreSQL
**When** a função `getPosicaoFiscalMetrics(portalSlug: string, ano: number)` é chamada
**Then** ela executa uma query Kysely simples `.selectFrom('fct_posicao_fiscal_metricas').where('portal_slug', '=', portalSlug).where('ano', '=', ano).executeTakeFirst()`.
**And** ela não contém nenhuma chamada a `sql` bruto com `SUM()`, `AVG()` ou `GROUP BY` sobre dados transacionais.
**And** o parâmetro `portalSlug` é obrigatório no contrato de tipos.
**And** o teste de paridade TypeScript `make test/ts` passa sem erros de tipagem.

### Story 2.2: Leitores Burros Atômicos para Domínios Específicos (Despesas, Receitas, CAPREM e Saúde)

As a developer,
I want atomic Kysely reader functions for expense analysis, budget execution, CAPREM actuarial history, and Health story metrics in `@transparencia/db`,
So that all backend queries act strictly as pass-through DTO providers with zero runtime SQL logic, hardcoded dictionaries, or type casting.

**Acceptance Criteria:**

**Given** os marts `fct_analise_despesas_metricas`, `fct_execucao_orcamentaria_metricas`, `fct_historia_caprem_metricas` e `fct_historia_saude_metricas`
**When** as funções leitoras `getAnaliseDespesasMetrics`, `getExecucaoOrcamentariaMetrics`, `getHistoriaCapremMetrics` e `getHistoriaSaudeMetrics` são invocadas
**Then** todas realizam estritamente `.selectFrom(...)` aplicando obrigatoriamente a cláusula `.where('portal_slug', '=', portalSlug)`.
**And** o código legado monolítico de agregação e filtros runtime em `@transparencia/db/src/queries/historia_caprem.ts` e `historia_saude.ts` (incluindo `ELEMENTO_LABELS` hardcoded) é removido.
**And** a suíte de testes de tipos `make test/ts` é aprovada com 100% de sucesso.

---

## Epic 3: Reorganização da UI e Co-localização de Loaders no `apps/web`

Refatorar a camada de apresentação separando primitivas de design system em `packages/ui` de componentes de domínio em `apps/web/components/`, co-localizando data loaders e View Models em `apps/web/app/` e garantindo 100% de preservação da paridade visual e funcional existente.

### Story 3.1: Desacoplamento da UI - Migração dos Componentes de Domínio para `apps/web/components/`

As a frontend developer,
I want domain-specific UI components moved from `packages/ui` to `apps/web/components/`,
So that `packages/ui` contains only generic, agnostic design system primitives.

**Acceptance Criteria:**

**Given** componentes de domínio como `posicao-fiscal-hero.tsx`, `caprem-hero-section.tsx`, `saude-emendas-section.tsx` em `packages/ui`
**When** a reorganização dos pacotes é executada
**Then** todos os componentes específicos de domínio são movidos para o diretório plano `apps/web/components/`.
**And** em `packages/ui/src/components/` permanecem exclusivamente primitivas agnósticas de design system (ex: `button.tsx`, `card.tsx`, `dense-table.tsx`, `kpi-card.tsx`).
**And** todas as importações no `apps/web` são atualizadas sem causar falhas de compilação no `pnpm build`.

### Story 3.2: Co-localização de Data Loaders e View Models em `apps/web/app/`

As a developer,
I want page data loaders and View Model composition co-located near their Next.js routes in `apps/web/app/`,
So that pages fetch DTOs via `@transparencia/db` atomic readers and pass ready props to domain UI components.

**Acceptance Criteria:**

**Given** as rotas de páginas em `apps/web/app/` (Posição Fiscal, Despesas, Saúde, CAPREM, Receitas)
**When** os data loaders são configurados nas rotas de `apps/web/app/` (incluindo `apps/web/app/[portalSlug]/caprem/page.tsx`)
**Then** os data loaders buscam os dados utilizando exclusivamente os leitores atômicos do `@transparencia/db` (ex: `getHistoriaCapremMetrics(portalSlug, ano)`).
**And** os componentes de UI de domínio em `apps/web/components/` recebem DTOs prontos como props.
**And** 100% da paridade visual e funcional de todas as telas existentes é rigorosamente preservada sem remoção de nenhuma visualização ou gráfico (NFR5).
**And** as suítes de validação `make test`, `make test/ts` e `pnpm build` passam com sucesso.

### Story 3.3: Migração Completa dos Loaders Web para Leitores de Métricas

As a developer,
I want all route loaders in `apps/web/app/[portalSlug]` to consume the new `*-metrics` readers from `@transparencia/db` wherever coverage exists,
So that the application fully realizes the architecture of pre-materialized metrics marts and removes residual dependence on legacy monolithic readers.

**Acceptance Criteria:**

**Given** os leitores atômicos de métricas já existentes em `@transparencia/db` (ex: `getPosicaoFiscalMetrics`, `getAnaliseDespesasMetrics`, `getExecucaoOrcamentariaMetrics`, `getFontesReceitaMetrics`, `getHistoriaCapremMetrics`, `getHistoriaSaudeMetrics`)
**When** os loaders das rotas de domínio em `apps/web/app/[portalSlug]/` são refatorados
**Then** toda rota com cobertura de métricas disponível passa a buscar dados exclusivamente via leitores `*-metrics`, preservando o filtro obrigatório por `portalSlug`.

**And** o objetivo desta story é eliminar a dependência dos readers legados atuais na aplicação web para os domínios cobertos, mantendo apenas fluxos orientados a métricas.

**And** para cada domínio sem cobertura total de DTO métrico (campos detalhados ainda não materializados), deve ser aberto e documentado um plano de extensão de métricas no dbt, analisado caso a caso (uma métrica por vez), com decisão explícita de implementação antes de qualquer mudança no loader.

**And** qualquer fallback legado temporário deve ser excepcional, explicitamente rastreado com prazo de remoção no artefato da story, e não pode ser considerado estado final da migração.

**And** nenhum loader de rota principal deve depender de agregação runtime em TypeScript para totais fiscais já cobertos por marts de métricas.

**And** todos os contratos de props dos componentes em `apps/web/components/` permanecem estáveis, preservando 100% da paridade visual e funcional existente (NFR5).

**And** a suíte completa de validação (`make test`, `make test/ts`, `pnpm build`) passa com sucesso.

**And** é produzido um mapa de rastreabilidade por rota (reader legado anterior -> reader de métricas adotado -> gaps remanescentes -> decisão de implementação dbt), anexado aos artefatos da implementação.

### Plano Pós-Story 3.3 (Aposentadoria Completa do Legado)

Objetivo: eliminar toda dependência residual de queries legadas nos domínios cobertos e completar cobertura métrica para Pessoal e Licitações.

#### Story 3.4: Validação Final e Gate de Encerramento da Story 3.3

As a developer,
I want to execute the full validation gate (`make test`, `make test/ts`, `pnpm build`) and register evidence,
So that Story 3.3 closes with objective proof of stability before expanding scope.

Entregáveis:
- Evidências dos três comandos no artefato da story.
- Checklist 3.3 totalmente concluído.

#### Story 3.5: Complemento Métrico de Visão Geral e Orçamento

As a data+web developer,
I want to expand metrics coverage for fiscal details and budget functional breakdown,
So that `loadVisaoGeralData` e `loadOrcamentoData` removam fallbacks legados restantes.

Entregáveis:
- Extensão dos marts para restos pendentes/top credores e dimensão funcional consolidada.
- Readers de métricas correspondentes em `@transparencia/db`.
- Remoção de fallback legado nesses dois loaders.

#### Story 3.6: Complemento Métrico de Despesas, Saúde e CAPREM

As a data+web developer,
I want metrics for HHI/diárias/restos (Despesas), tendência/contratação/fontes (Saúde) e séries/natureza/cadprev (CAPREM),
So that these domains stop depending on legacy query composition.

Entregáveis:
- Novos/ajustados marts em `elt/transform/models/marts/metrics/`.
- Readers `*-metrics` dedicados para os blocos faltantes.
- Remoção dos fallbacks controlados nos três loaders.

#### Story 3.7: Métricas de Pessoal e Licitações (Cobertura Total)

As a data+web developer,
I want to create dedicated marts/readers for Pessoal and Licitações,
So that both routes migrate from 100% legacy to 100% metrics.

Entregáveis:
- `fct_pessoal_metricas` e `fct_licitacoes_metricas` (ou partições equivalentes por subdomínio).
- Readers de métricas para folha/chefias/13o/proventos/departamental e gaps/adesão/anomalias/modalidades.
- Migração completa de `apps/web/app/[portalSlug]/pessoal/loader.ts` e `apps/web/app/[portalSlug]/licitacoes/loader.ts`.

#### Story 3.8: Hard Cutover e Remoção Definitiva do Legado

As a maintainer,
I want to remove legacy query paths no longer needed,
So that architecture remains SSOT via dbt marts + atomic metric readers.

Entregáveis:
- Remoção de imports/chamadas legadas substituídas.
- Atualização de testes de paridade para contratos métricos finais.
- Changelog de aposentadoria do legado por domínio.

Critérios de saída da fase:
- Nenhum loader de rota principal depende de agregação runtime para domínios cobertos.
- `portalSlug` explícito em todos os fluxos da web.
- Suíte completa verde em cada story de corte (`make test`, `make test/ts`, `pnpm build`).

---

## Epic 4: Experiência Visual, Responsividade Mobile, SEO & Otimização para LLMs

Garantir que a plataforma TransparenciaWeb seja visualmente impecável em dispositivos móveis, com títulos dinâmicos padronizados, suporte a favicon personalizável (corrigindo a colisão de rota do Next.js no loader dinâmico), totalmente otimizada para motores de busca (SEO) e consumo automatizado por LLMs/IAs, além de alinhar as diretrizes de código do repositório em todo o código TypeScript/Frontend.

### Story 4.1: Correção de Roteamento do Favicon e Suporte a Ícones Personalizados

As a platform user / auditor,
I want the application to serve favicon requests properly without triggering server route exceptions,
So that browser tab icons render correctly and metric loaders are not invoked for static assets like `favicon.ico`.

**Acceptance Criteria:**
- **Given** uma requisição estática para `GET /favicon.ico`
- **When** o servidor Next.js processa a rota
- **Then** a requisição não deve colidir com o parâmetro dinâmico `[portalSlug]` de `app/[portalSlug]`.
- **And** a função `requireEmpresaIdsForMetrics` nunca deve ser invocada com o slug `"favicon.ico"`.
- **And** a aplicação deve expor suporte completo no Next.js Metadata (`metadata.icons`) para carregar o favicon fornecido pelo usuário.

### Story 4.2: Títulos Dinâmicos de Página com Prefixo TransparenciaWeb

As a portal visitor,
I want clear, descriptive page titles with the `TransparenciaWeb` prefix on every page,
So that I can immediately identify the current section and municipal entity in my browser tabs and bookmarks.

**Acceptance Criteria:**
- **Given** qualquer página renderizada no portal (ex: `/visao-geral`, `/despesas`, `/caprem`, `/saude`)
- **When** a página é carregada no navegador
- **Then** o título HTML da página deve seguir a estrutura `TransparenciaWeb - [Nome da Tela] | [Entidade do Portal]`.
- **And** o `layout.tsx` raiz do Next.js deve definir um `title.template` padronizado.

### Story 4.3: Responsividade Mobile e Adequação para Telas Menores

As a mobile device user,
I want tables, KPI cards, navigation menus, and year selectors to adapt to smaller screens,
So that I can consult public transparency data smoothly on smartphones and tablets.

**Acceptance Criteria:**
- **Given** um dispositivo móvel com largura de tela entre 360px e 430px
- **When** o usuário navega pelas telas do portal
- **Then** as tabelas (`dense-table`, tabelas de despesas e contratos) devem possuir rolagem horizontal suave ou layout adaptativo sem quebrar o container.
- **And** componentes de KPI (`kpi-card`) e seletores de filtros devem reorganizar-se em colunas responsivas utilizando breakpoints Tailwind (`sm:`, `md:`).
- **And** botões e elementos interativos devem possuir área de toque mínima adequada (44x44px).

### Story 4.4: Investigação e Correção de Emendas via PIX Zeradas em "Recebido por Emendas Parlamentares"

As a municipal transparency user / auditor,
I want "Recebido por emendas parlamentares" and "Emendas PIX" metrics to correctly reflect the data present in `raw.emendas_cad`,
So that PIX transfer amendments are accurately reported in the portal header and revenues dashboard instead of showing zero.

**Acceptance Criteria:**
- **Given** registros de emendas via PIX cadastrados na tabela `raw.emendas_cad` (`stg_porciuncula_prefeitura__emendas_cad`)
- **When** os modelos dbt (`int_emendas_consolidadas.sql`, `fct_emendas.sql` e `fct_fontes_receita_metricas.sql`) forem processados e agregados
- **Then** a identificação/categorização de emendas PIX vs. individuais em `fct_emendas` deve capturar corretamente as modalidades/tipos de transferência PIX.
- **And** o modelo de métricas `fct_fontes_receita_metricas` deve retornar o saldo `emendas_pix_arrecadado` maior que 0 quando existirem registros válidos.
- **And** o leitor Kysely (`getFontesReceitaMetrics`) e a UI (`EmendasCard` / `emendas-card.tsx` em "Recebido por emendas parlamentares") devem exibir o valor correto e não zerado.
- **And** a suíte de testes fiscais dbt (`make test`) e testes TypeScript (`make test/ts`) deve ser atualizada com asserções de paridade para validar a não zeragem.

### Story 4.5: Estruturação para Leitura por LLMs (LLM-Friendly App Architecture)

As an AI agent / LLM or accessibility screen reader,
I want structured HTML5 semantics, JSON-LD metadata, and a standard `/llms.txt` file,
So that I can extract, query, and process municipal transparency data accurately.

**Acceptance Criteria:**
- **Given** um agente de IA acessando a aplicação web
- **When** o agente analisa o código HTML e endpoints da aplicação
- **Then** o layout deve utilizar tags semânticas HTML5 (`<header>`, `<main>`, `<section>`, `<article>`, `<table>` acessíveis).
- **And** o portal deve disponibilizar os arquivos `/llms.txt` e `/llms-full.txt` detalhando as rotas, APIs e estrutura dos dados públicos.
- **And** as páginas principais devem conter esquemas `Schema.org` (`GovernmentOrganization`, `DataCatalog`, `Dataset`) serializados em JSON-LD.

### Story 4.6: SEO Básico (Meta Tags, Open Graph, Sitemap & Robots)

As a municipal transparency manager,
I want the portal to feature full search engine metadata and social sharing previews,
So that citizens can easily find transparency information on search engines and social platforms.

**Acceptance Criteria:**
- **Given** indexadores de busca ou crawlers de redes sociais
- **When** o portal é indexado ou compartilhado
- **Then** o Next.js Metadata API deve fornecer meta tags dinâmicas de `description`, `keywords`, `canonical` e `robots`.
- **And** meta tags Open Graph (`og:title`, `og:description`, `og:image`, `og:type`, `og:site_name`) e Twitter Cards devem estar configuradas.
- **And** rotas para `sitemap.xml` dinâmico e `robots.txt` devem estar ativas e válidas.

### Story 4.7: Suporte a PWA (Progressive Web App - Instalabilidade e Notificações de Extração)

As a municipal portal user / citizen,
I want the TransparenciaWeb platform to function as a Progressive Web App (PWA) that is installable on my mobile or desktop browser and capable of sending push notifications when new municipal extraction data is published,
So that I can quickly access transparency data from my home screen and stay immediately informed of new fiscal data updates.

**Acceptance Criteria:**
- **Given** um munícipe acessando a aplicação web em um navegador compatível (Chrome, Safari, Edge, Firefox)
- **When** o portal é carregado
- **Then** a aplicação deve fornecer um arquivo Web App Manifest (`manifest.webmanifest` ou `manifest.json`) configurado com `name: "TransparenciaWeb - Transparência Pública Municipal"`, `short_name: "TransparenciaWeb"`, `theme_color: "#1e3a8a"`, `background_color: "#0f172a"`, `display: "standalone"`, `start_url: "/"`, e ícones em resoluções 192x192 e 512x512.
- **And** o navegador deve habilitar o prompt nativo de instalação ("Adicionar à Tela de Início" / "Instalar App").
- **And** o Service Worker (`sw.js`) deve ser registrado para gerenciar cache estático e suporte offline do app shell.
- **And** a aplicação deve integrar com a Web Push / Notification API para alertar o usuário quando a data de extração (`dataExtracao` em `dim_portais`) for atualizada no banco de dados.

### Story 4.8: Aplicação de Diretrizes do Projeto no Código Frontend (Non-Python Files)

As a code maintainer,
I want all TypeScript, React components, and styling files to strictly comply with `AGENTS.md` guidelines,
So that code readability, immutability, explicit metric naming, and type safety are enforced across the workspace.

**Acceptance Criteria:**
- **Given** o repositório de código TypeScript em `apps/web`, `packages/ui` e `packages/db`
- **When** a auditoria e refatoração de código for concluída
- **Then** todas as variáveis de métrica e DTOs devem utilizar nomes explícitos (zero abreviações opacas).
- **And** transformações de dados devem ser puras e imutáveis (`.map`, `.filter`, `.reduce`).
- **And** as suítes de validação (`pnpm build` e `pnpm test`) devem rodar 100% limpas e sem warnings de tipagem.

### Story 4.9: Modelagem dbt e Exibição de Receitas Extra-Orçamentárias no Portal

As a municipal transparency user / auditor,
I want extra-budgetary revenues (such as tax retentions, consignments, deposits, and payroll loans) modeled in dbt and presented on the Receitas page,
So that citizens have complete visibility over all financial inflows managed by the municipality alongside budgetary revenues.

**Acceptance Criteria:**
- **Given** a tabela raw `receita_extra_orcamentaria` (já declarada no `_sources.yml`)
- **When** o modelo de staging `stg_porciuncula_prefeitura__receita_extra_orcamentaria.sql` for executado no dbt
- **Then** os dados de entrada de receitas extra-orçamentárias devem ser normalizados com o campo `portal_slug` e tipos padronizados (`ano`, `empresa`, `codigo`, `descricao`, `valor`, `dtlan`, `empresanome`).
- **And** os dados extra-orçamentários devem ser integrados no modelo intermediário unificado `int_receitas_consolidadas.sql` sob o classificador `tipo_receita = 'extra_orcamentaria'`, evitando a criação desnecessária de novos modelos `int_`.
- **And** os modelos marts `fct_receita_extra_orcamentaria.sql` (para listagem detalhada) e `fct_fontes_receita_metricas.sql` (para agregação da métrica `receita_extra_orcamentaria_arrecadado`) devem ser criados/estendidos com materialização física (`materialized='table'`), consolidando totais e listagens por `portal_slug` e `ano`.
- **And** no pacote `@transparencia/db`, o leitor `getFontesReceitaMetrics` deve ser estendido para incluir `receitaExtraOrcamentariaArrecadado` e a leitora `getReceitasExtraOrcamentariasList` deve ser criada aplicando obrigatoriamente o filtro `portal_slug`.
- **And** na aplicação web (`apps/web/app/[portalSlug]/receitas`), o loader e a View Model devem consumir as novas métricas e exibir um novo card de KPI ("Receitas Extra-Orçamentárias") no resumo de receitas e uma tabela detalhada de lançamentos extra-orçamentários na interface.
- **And** os arquivos `apps/web/public/llms.txt` e `apps/web/public/llms-full.txt` devem ser atualizados conforme a Regra 12 de `AGENTS.md` para documentar o novo conjunto de dados públicos.
- **And** as suítes de validação (`make test`, `make test/ts` e `pnpm build`) devem passar com 100% de sucesso.

### Story 4.13: Parametrização Dinâmica de Limites Fiscais (Seed `seed_constantes_fiscais`) na UI de Licitações

As a municipal transparency user / auditor,
I want the Licitações page to dynamically display the exact legal limits for bidding exemptions (limites de dispensa) corresponding to the selected fiscal year (exercício),
So that explanation texts and alert tooltips reflect the actual decree/law applicable for that year (e.g. Decreto 12.343/2024 for 2025 vs Decreto 12.807/2025 for 2026) without hardcoded static amounts.

**Acceptance Criteria:**
- **Given** o seed `seed_constantes_fiscais.csv` contendo os limites históricos e vigentes de dispensa de licitação (`limite_dispensa_compras_servicos`, `limite_dispensa_obras_engenharia`, `limite_dispensa_veiculos`) por período de ano
- **When** o usuário seleciona um ano/exercício específico na rota `/licitacoes` (ex: 2023, 2024, 2025, 2026)
- **Then** a função leitora/loader de métricas de licitação (`getLicitacoesMetrics`) em `@transparencia/db` deve expor o valor numérico do limite de dispensa de compras/serviços vigente no ano selecionado (`limiteDispensaComprasServicos`).
- **And** o texto explicativo no cabeçalho de `apps/web/app/[portalSlug]/licitacoes/page.tsx` deve formatar dinamicamente o valor retornado (substituindo o valor fixo hardcoded de `R$ 62.725,59` por `acima de R$ {limiteDispensaFormatado} sem licitação`), explicitando a base legal correspondente ao exercício exibido.
- **And** as suítes de validação (`make test`, `make test/ts` e `pnpm build`) devem passar com 100% de sucesso.

### Story 4.14: Derivação de Status de Inexecução Contratual e Filtro de Segmentação de Execução na UI

As a citizen / municipal transparency auditor,
I want the contracts list and section to classify expired contracts with zero execution (`liquidado = 0` / `pago = 0`) as unexecuted/rescinded and provide an execution status filter,
So that unexecuted contracts are cleanly segregated from active/executed contracts without cluttering contract cards with excess text or hidden tooltips.

**Acceptance Criteria:**
- **Given** o modelo dbt `fct_contratos_servicos_vigentes.sql` e os componentes UI em `apps/web/components/contratos-servicos-vigentes-section.tsx` e `contrato-servico-vigente-card.tsx`
- **When** um contrato possui data de vencimento anterior ao ano/data atual e apresenta liquidação zerada (`total_liquidado = 0`)
- **Then** a leitora `@transparencia/db` / View Model da página deve derivar a propriedade de status de execução (ex: `statusExecucao: 'inexecutado' | 'em_execucao' | 'concluido'`).
- **And** a UI da seção de contratos deve fornecer um filtro de segmentação limpo por status de execução (ex: `Em Execução` [padrão], `Concluídos`, `Não Executados`), permitindo ao usuário auditar contratos inexecutados sob demanda sem poluir visualmente os cards padrão.
- **And** para contratos classificados como não executados na visão filtrada, exibir apenas um badge de status simples e minimalista (ex: badge neutro `Sem Execução Orçamentária` / `Não Executado`), sem adicionar blocos de texto explicativo ou tooltips nos cards.
- **And** os arquivos `apps/web/public/llms.txt` e `apps/web/public/llms-full.txt` devem ser atualizados caso novos campos públicos de status de execução sejam expostos.
- **And** as suítes de validação (`make test`, `make test/ts` e `pnpm build`) devem passar com 100% de sucesso.

### Story 4.15: Revelação Progressiva e Segregação Didática de Restos a Pagar e Contratos Plurianuais na UI

As a citizen / municipal auditor,
I want the Restos a Pagar cards and Contract detail drawers to segregate processed vs unprocessed liabilities and multi-year contract celebration years using progressive disclosure,
So that I can clearly audit financial obligations without cluttering the main UI with redundant badges or text boxes.

**Acceptance Criteria:**
- **Given** os componentes de Posição Fiscal e Licitações/Contratos em `apps/web/components/` (ex: `posicao-fiscal-hero.tsx`, `contratos-servicos-vigentes-section.tsx`, `contrato-servico-vigente-card.tsx`)
- **When** o usuário visualiza o card de Restos a Pagar no painel de Posição Fiscal ou abre o Drawer de Detalhes de um contrato plurianual
- **Then** o card principal de Restos a Pagar deve apresentar um indicador discreto de informação `(i)` com tooltip simples em hover explicando a diferença entre Restos Processados (dívidas de serviços já prestados) e Não Processados (obras/serviços contratados em andamento).
- **And** no Drawer de Detalhes ao clicar no card ou contrato, exibir a segregação por mandato de origem (`Gestão Atual [2025-2028]` vs `Gestões Anteriores [Pré-2025]`) e as datas de celebração/vigência de contratos plurianuais.
- **And** a listagem principal deve permanecer limpa, sem adição de blocos de texto promocionais ou badges ruidosos que causem poluição visual ou sobrecarga cognitiva na UI principal.
- **And** os arquivos `apps/web/public/llms.txt` e `apps/web/public/llms-full.txt` devem ser atualizados caso novos campos públicos de segregação de restos ou vigências contábeis sejam expostos.
- **And** as suítes de validação (`make test`, `make test/ts` e `pnpm build`) devem passar com 100% de sucesso.

---


## Epic 5: Arquitetura Analytics Serverless (DuckDB + Parquet R2), Servidor MCP & Assistente Fiscal com Evals

### Overview
Evolução da camada de inteligência de dados de transparência fiscal para uma arquitetura moderna baseada em **MCP (Model Context Protocol)**, DuckDB-WASM e arquivos Parquet particionados hospedados no Cloudflare R2, agregando uma camada de contexto orientada a **Skills (Markdown)** e um **Harness de Avaliação Determinística (Evals)**, alinhada às melhores práticas de agentes de IA (posthog.com/newsletter/building-ai-agents).

> [!NOTE]
> **Decisão Arquitetural (Evolução por Adição + MCP First):**
> Manter o pipeline dbt/PostgreSQL 100% intocado para garantir os testes de integração fiscais. Uma etapa pós-materialização exporta os marts do PostgreSQL para arquivos `.parquet` comprimidos (Snappy) e os sincroniza com o Cloudflare R2.
> A camada de inteligência expõe os marts através de um **Servidor/Ferramentas MCP** (`transparencia-mcp`), permitindo que tanto o assistente no frontend quanto agentes LLM externos consultem os dados com 100% de exatidão fiscal.

---

### Story 5.1: Exportação Automatizada de Marts PostgreSQL para `.parquet` Snappy e Sync MinIO/R2

As a data engineer,
I want a Python/DuckDB post-processing script (`elt/export_marts_parquet.py`) and sync script (`elt/scripts/sync_parquet.py`) that export all Postgres marts to Parquet and upload to Cloudflare R2 / MinIO,
So that we maintain a clean Parquet analytics store without altering the dbt Postgres adapter or integration tests.

**Acceptance Criteria:**
- **Given** o banco PostgreSQL populado com os marts de métricas materializados (`fct_*_metricas`, `dim_*`, `seed_*`) pós-execução do dbt
- **When** o script `elt/export_marts_parquet.py` é executado
- **Then** ele conecta ao PostgreSQL via DuckDB nativo (com fallback SQLAlchemy/pandas) e exporta cada mart para `target/parquet/` em formato `.parquet` comprimido com Snappy.
- **And** o script `elt/scripts/sync_parquet.py` sincroniza os arquivos para o Cloudflare R2 (produção) ou MinIO S3 local (dev), verificando ETag/ContentLength para evitar re-uploads.
- **And** a suíte de testes `elt/tests/test_export_marts_parquet.py` e `test_sync_parquet.py` executa e passa com 100% de sucesso.

---

### Story 5.2: Motor de Execução DuckDB-WASM e Registro Dinâmico dos 25 Marts Parquet (`duckdb-executor.ts`)

As a fullstack developer,
I want an atomic DuckDB-WASM execution module (`apps/web/lib/duckdb-executor.ts`) that runs server-side (Node.js) and client-side (Browser),
So that SQL queries against Parquet files hosted on R2/MinIO execute instantly with automatic `HugeInt` 128-bit casting.

**Acceptance Criteria:**
- **Given** os 25 arquivos Parquet de marts (`MART_TABLES`) armazenados no R2 ou sistema de arquivos local
- **When** a função `getDuckDbInstance()` ou `queryDuckDbParquet(sql)` é invocada no `apps/web`
- **Then** o DuckDB-WASM é inicializado via `eval("require")` no Node.js (Vercel Serverless) ou `Web Worker` no navegador.
- **And** todas as 25 tabelas fato/dimensão são registradas como views relacionais nativas no DuckDB.
- **And** valores numéricos de somatórios fiscais são protegidos por `CAST AS DOUBLE` prevenindo falhas de conversão de 128-bit.

---

### Story 5.3: Servidor & Ferramentas MCP (`transparencia-mcp`) para Consulta Dinâmica e Taxonomia Fiscal

As a developer / AI ecosystem user,
I want a Model Context Protocol (MCP) server exposing tools to inspect taxonomia, schema definitions, and execute analytical DuckDB queries,
So that internal web chat agents and external LLM agents (Claude, ChatGPT, etc.) query municipal transparency data via a standard, secure protocol.

**Acceptance Criteria:**
- **Given** o repositório TransparenciaWeb
- **When** um agente de IA acessa o servidor MCP `transparencia-mcp` (ou endpoint MCP em Next.js)
- **Then** as ferramentas MCP `list_marts_taxonomia`, `get_mart_schema` e `query_duckdb_mart` são expostas com JSON Schema estrito.
- **And** a ferramenta de taxonomia permite ao agente explorar tabelas, dimensões e colunas sob demanda sem entupir o prompt inicial com todo o schema do banco.

---

### Story 5.4: Camada de Contexto & Skills em Markdown (Regras Fiscais STN/MCASP)

As an AI prompt engineer / data architect,
I want structured Markdown Skills detailing accounting rules (STN/MCASP), fiscal formulas, Restos a Pagar rules, and domain-specific query patterns,
So that the AI agent generates accurate DuckDB queries without domain or accounting hallucinations.

**Acceptance Criteria:**
- **Given** a documentação de regras de negócio contábeis em `_bmad/skills/` ou `apps/web/lib/skills/`
- **When** o assistente fiscal prepara a chamada ao LLM
- **Then** o sistema injeta a Skill correspondente ao domínio solicitado (Posição Fiscal, CAPREM, Saúde, Licitações, Pessoal).
- **And** o prompt combina **Layered Runtime Context Injection** (`portal_slug` ativo, ano do exercício selecionado, rota atual).

---

### Story 5.5: Assistente Fiscal no Frontend (`assistant-chat-drawer.tsx` + Tool Calling, Charts & Feedback Telemetry)

As a citizen / auditor,
I want an interactive chat drawer accessible from the header featuring suggested questions, formatted answers, KPI cards, charts, and feedback buttons (Thumbs Up / Down),
So that I can explore municipal transparency data in natural language with visual evidence and rate response quality in real-time.

**Acceptance Criteria:**
- **Given** o botão "Perguntar aos Dados" no cabeçalho do portal
- **When** o usuário abre o `assistant-chat-drawer.tsx` e envia uma pergunta
- **Then** o backend invoca o LLM via Tool Calling / ReAct executando a query DuckDB correspondente.
- **And** a resposta renderiza a explicação textual, KPI cards formatados (`fmtMoney`), gráfico dinâmico (barras/linhas) e a query SQL gerada para auditoria do cidadão.
- **And** cada resposta do assistente renderiza botões de avaliação rápida (👍 Útil / 👎 Impreciso) que disparam o evento de telemetria `ai_feedback` (`score`, `message_id`, `answer_snippet`, `portal_slug`, `ano`) diretamente para o PostHog.

---

### Story 5.6: Harness de Avaliação Determinística (Evals) & Suíte de Testes de Paridade de IA (`make test/evals`)

As a quality engineer,
I want an automated Evals test harness (`make test/evals` ou `pnpm test`) running benchmark questions against the agent,
So that regressions, hallucinations, or wrong calculation outputs are caught before deployment.

**Acceptance Criteria:**
- **Given** um conjunto de mais de 50 perguntas de benchmark (ex: `eval-12` testando retenção patronal e rombo previdenciário do CAPREM) com gabarito fiscal extraído dos marts dbt
- **When** o comando `make test/evals` ou `pnpm test` é executado
- **Then** o harness dispara as perguntas para a pipeline do assistente/MCP e compara os valores numéricos gerados contra o gabarito.
- **And** o teste falha se a discrepância percentual for maior que 0% em métricas contábeis.

---

### Story 5.7 (Deferred / Post-V1): Avaliador Automatizado (*LLM-as-a-Judge*) & Webhooks de Qualidade no PostHog

As a lead AI engineer / product manager,
I want an automated LLM-as-a-Judge pipeline that periodically audits production conversation traces from PostHog and alerts on low-score feedbacks,
So that we continuously measure agent accuracy, catch edge-case hallucinations, and auto-generate benchmark test cases without manual log inspection.

**Acceptance Criteria (Deferred):**
- **Given** as gerações de IA registradas no PostHog via evento `$ai_generation` e os feedbacks negativos via `ai_feedback` (`score: -1`)
- **When** o cron/worker de avaliação diária (*LLM-as-a-Judge*) é executado à meia-noite
- **Then** ele lê todas as respostas do dia no PostHog, submete a um modelo avaliador (Gemini 3.6 Flash) para checar a fidelidade contra os resultados SQL do DuckDB e gera um relatório diário de acurácia (ex: 98.4% de precisão).
- **And** webhooks automatizados notificam o time via Slack/E-mail imediatamente quando um feedback `score: -1` (👎) for capturado no PostHog.
- **And** as interações reais que geraram dúvidas ou imprecisões são convertidas automaticamente em novos casos de teste no `benchmark-questions.ts`.

---

### Story 5.8: Limpeza do DuckDB-WASM e Migração da IA para PostgreSQL

As a fullstack developer,
I want to remove the experimental DuckDB-WASM execution infrastructure and align AI/MCP tools to execute directly against Supabase PostgreSQL via `@transparencia/db`,
So that we eliminate cold-start issues, network timeouts (10s), Vercel bundle size limits (50MB), and dynamic WASM downloads to `/tmp`.

**Acceptance Criteria:**
- **Given** o módulo `apps/web/lib/duckdb-executor.ts`
- **When** o código é refatorado
- **Then** a dependência `@duckdb/duckdb-wasm`, downloads para `/tmp` e conexões com o MotherDuck são eliminados.
- **And** a função `queryDuckDbParquet` invoca a função `executeRawSql` exposta em `@transparencia/db` utilizando Kysely sobre PostgreSQL.
- **And** a configuração `next.config.js` é limpa de entradas de WASM e `package.json` remove a dependência.
- **And** todas as suítes de testes (`pnpm test`) e compilação (`pnpm build`) passam com 100% de sucesso.

---

### Story 5.9: Otimização de Índices e Performance no Supabase PostgreSQL

As a database architect,
I want functional indexes on `unaccent(lower(...))` and a strict `statement_timeout` configured in Supabase Postgres,
So that text search queries run instantly and abusive queries are automatically terminated without degrading web dashboard performance.

**Acceptance Criteria:**
- **Given** o banco de dados PostgreSQL gerenciado no Supabase
- **When** o script de otimização de índices for executado
- **Then** as extensões `unaccent` e `pg_trgm` são ativadas.
- **And** índices expressionais btree em `unaccent(lower(...))` são criados para as colunas de busca em `fct_despesas`, `fct_licitacoes` e `dim_credor`.
- **And** a role do Postgres ou conexões do assistente configuram `statement_timeout = '5000ms'` (5 segundos).

---

### Story 5.10: Trava de Segurança e Rate Limiting no MCP / Vercel Edge

As a backend engineer,
I want a Rate Limiting middleware at the Vercel Edge / API layer limiting anonymous users to 5 queries per day,
So that public infrastructure is protected from automated abuse and scraping.

**Acceptance Criteria:**
- **Given** uma requisição de usuário anônimo enviada para `/api/mcp` ou assistente
- **When** o usuário atinge o limite de 5 consultas em 24 horas
- **Then** o servidor responde com erro HTTP 429 (`QUOTA_EXCEEDED` com `code: "ANONYMOUS_LIMIT_REACHED"`).
- **And** clientes MCP externos exigem chave de API assinada (`API_KEY`) para requisições ilimitadas.

---

### Story 5.11: Funil de Conversão (Segway UI) e Integração Supabase Auth no Assistente

As a product manager / UX designer,
I want the assistant chat drawer to display remaining anonymous queries and present a seamless sign-up modal via Supabase Auth upon reaching the limit,
So that free users are smoothly converted into registered users to unlock full historical access and benefits.

**Acceptance Criteria:**
- **Given** o componente de chat do assistente em `assistant-chat-drawer.tsx`
- **When** o usuário interage com o assistente
- **Then** o topo da gaveta exibe o contador discreto de perguntas restantes.
- **And** ao receber o status 429 (`QUOTA_EXCEEDED`), a UI abre o modal de cadastro via Supabase Auth (Google / Magic Link).
- **And** após a autenticação, a cota do usuário é ampliada e o acesso histórico completo é desbloqueado.









