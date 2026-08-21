---
name: dbt-transparencia
description: Use when creating or editing dbt models, seeds, sources or schema contracts in this project
---

# dbt — Padrões do Projeto Transparência

## Arquitetura em 3 Camadas

```
raw_<portal_slug>.*        ← carregado por elt/load/run.py
  └─ staging/<portal>/     ← limpa, renomeia, faz casts
       └─ intermediate/    ← UNION ALL entre portais
            └─ marts/      ← dims + facts expostos ao dashboard
```

**Regra de ouro:** nunca pule camadas. Um mart nunca lê diretamente de um source — sempre passa por staging e intermediate.

---

## Convenções SQL (sem exceções)

- **Keywords em lowercase**: `select`, `from`, `where`, `left join`, `group by`, `with`, `as`, `coalesce`, `nullif`, `extract`, `distinct on`
- **Sem alinhamento de colunas**: não use espaços para alinhar `as`; deixa cada coluna na mesma indentação
- **Tipos**: sempre `text`, nunca `varchar`. Numéricos: `numeric(15, 2)`. Inteiros: `int`
- **Nunca use `select *`**: sempre liste as colunas explicitamente em todos os models (staging, intermediate e marts)
- **Nomes de colunas e métricas explícitos**: **Evite estritamente abreviações opacas em colunas de métricas** (ex: `c_valor`, `c_empenhado`, `df`, `do`, `pct`). Use sempre nomes 100% claros e descritivos: `valor_contrato`, `empenhado_contrato`, `percentual_folha`, `total_folha`, `total_pago`, etc.
- **Valores fixos/códigos em lowercase snake_case**: É estritamente proibido gravar strings formatadas para exibição em colunas de código/categoria/modalidade (ex: `'Adesão a ata (externa)'`, `'Sem licitação'`). Use sempre **lowercase snake_case** (ex: `'adesao_ata_externa'`, `'sem_licitacao'`, `'gap_licitacao'`, `'licitacao_propria'`). A formatação amigável é responsabilidade exclusiva da UI.
- **Insensibilidade a Acentuação e Caixa em Filtros de Texto (`unaccent`)**: Ao realizar comparações ou buscas por padrões de texto (`like`, `ilike` ou `case when`) em colunas de descrição, modalidade ou resumo (ex: `descricao`, `resumo`, `tipo_emenda`, `destinacao`), **é obrigatório** aplicar `{{ target.schema }}.unaccent(lower(...))` (ou `unaccent`) para evitar falhas de categorização por variações de acentuação ou caixa na fonte de dados (ex: `'TRANSFERÊNCIA ESPECIAL'` vs `'transferencia especial'`).


```sql
-- ✅ correto
select
    ano::int as ano,
    nullif(replace(empenhado, ',', '.'), '')::numeric(15, 2) as empenhado,
    nullif(data_empenho, '')::date as data_empenho,
    nomefor as fornecedor_nome

-- ❌ errado
SELECT
    ano::INT                     AS ano,
    NULLIF(REPLACE(empenhado, ',', '.'), '')::NUMERIC(15,2)   AS empenhado
```

---

## Casts Padrão (dados raw são todos `text`)

| Tipo de dado               | Cast                                                 |
| -------------------------- | ---------------------------------------------------- |
| Inteiro                    | `col::int`                                           |
| Decimal BR (vírgula)       | `nullif(replace(col, ',', '.'), '')::numeric(15, 2)` |
| Data `dd/mm/yyyy hh:mm:ss` | `nullif(col, '')::date`                              |
| Texto limpo                | `nullif(trim(col), '')`                              |

---

## Chaves Surrogate

**Sempre** usar `dbt_utils.generate_surrogate_key`. **Sempre** incluir `portal_slug` como primeiro campo.

```sql
{{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'numero']) }} as licitacao_id
```

Instalar via `make dbt/deps` (requer `packages.yml` com `dbt-labs/dbt_utils`).

---

## Naming

| Camada        | Padrão                        | Exemplo                                      |
| ------------- | ----------------------------- | -------------------------------------------- |
| Staging       | `stg_<portal>__<tabela>.sql`  | `stg_porciuncula_prefeitura__licitacoes.sql` |
| Intermediate  | `int_<nome>.sql`              | `int_licitacoes_consolidadas.sql`            |
| Mart dimensão | `dim_<nome>.sql`              | `dim_licitacao.sql`                          |
| Mart fato     | `fct_<nome>.sql`              | `fct_despesas.sql`                           |
| Seed          | `seed_<portal>_<nome_pt>.csv` | `seed_porciuncula_prefeitura_orgaos.csv`     |

**Seeds:** nomes em português. Nunca usar termos em inglês (`entities` → `orgaos`, `suppliers` → `fornecedores`).

---

## Modelo Staging — Template

```sql
with source as (
    select * from {{ source('<portal>', '<tabela>') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        -- ... casts e renomeações (liste TODAS as colunas explicitamente)
    from source
)

-- ✅ liste as colunas — nunca use select *
select
    ano,
    empresa_id,
    -- ... todas as colunas do CTE renamed
from renamed
```

Source declarado em `models/staging/<portal>/_sources.yml`, schema: `raw_<portal_slug>`.

> **Proibido**: `select * from renamed`, `select *` em qualquer camada. Sempre liste as colunas.

---

## Responsabilidade de cada camada (grain e agregação)

**Staging** — relação 1:1 com a fonte. Somente renomear, castear e categorizar. **Nunca agregar, nunca fazer GROUP BY, nunca mudar o grain.** Se o dado bruto tiver duplicatas, elas devem subir para o intermediate intactas — staging não é o lugar de resolvê-las.

**Intermediate** — é o lugar correto para re-graining, deduplicação e UNION ALL entre portais. Quando a fonte pode emitir múltiplas linhas para a mesma chave de negócio (ex: mesmo código de receita com fontes STN distintas), o GROUP BY + SUM deve ocorrer aqui, após o UNION ALL:

```sql
-- int_<entidade>_consolidada.sql
with combined as (
    select ... from {{ ref('stg_portal_a__<tabela>') }}
    union all
    select ... from {{ ref('stg_portal_b__<tabela>') }}
)

-- agrega ao grain correto: uma linha por (portal_slug, tipo, ano, empresa_id, codigo)
select
    portal_slug,
    tipo,
    ano,
    empresa_id,
    codigo,
    max(descricao) as descricao,
    sum(valor_a) as valor_a,
    sum(valor_b) as valor_b
from combined
group by portal_slug, tipo, ano, empresa_id, codigo
```

**Marts** — consomem o intermediate já com o grain correto. Não fazem GROUP BY sobre dados hierárquicos brutos.

---

## Chaves Primárias na Camada Raw (elt/load)

A PK da tabela raw define o comportamento do upsert (`ON CONFLICT DO UPDATE`). Um PK insuficiente causa sobrescrita silenciosa de linhas quando o portal emite múltiplas linhas para a mesma chave aparente.

**Regra:** antes de definir `key_cols` para um endpoint, perguntar: *"O portal pode emitir mais de uma linha com esses valores de chave para o mesmo recurso, diferenciadas por alguma coluna discriminante?"* Se sim, incluir essa coluna discriminante na `key_cols`.

Exemplo: `receita_orcamentaria` tem `(ano, empresa, codigo)` como chave natural, mas o portal pode emitir múltiplas linhas por código quando há diferentes fontes STN. Solução: `key_cols=["ano", "empresa", "codigo", "fontestn"]` + garantir que `fontestn` nunca seja NULL (usar `''` como default para nós pai).

Colunas discriminantes comuns a monitorar: `fontestn`, `cod_aplicacao`, `mes`, `tipo`.

---

## Modelo Intermediate — Template Multi-Portal

```sql
with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        -- ... liste todas as colunas do staging (nunca use *)
    from {{ ref('stg_porciuncula_prefeitura__<tabela>') }}
)

-- novo portal: adicionar CTE + union all
-- ✅ liste as colunas — nunca use select *
select
    portal_slug,
    ano,
    empresa_id
    -- ...
from porciuncula
```

---

## Testes com dbt_expectations

Todos os `_<model>.yml` (staging, intermediate e marts) **devem** incluir testes usando `metaplane/dbt_expectations`. Use o bom senso para escolher os testes mais relevantes por camada.

### Testes típicos por tipo de coluna

```yaml
columns:
  - name: receita_id          # chave surrogate
    tests:
      - not_null
      - unique

  - name: ano                 # inteiro com range conhecido
    tests:
      - not_null
      - dbt_expectations.expect_column_values_to_be_between:
          min_value: 2015
          max_value: 2035

  - name: empenhado           # valor financeiro — nunca negativo nesta camada
    tests:
      - dbt_expectations.expect_column_values_to_be_between:
          min_value: 0
          row_condition: "empenhado is not null"

  - name: fornecedor_cpf_cnpj  # formato CPF/CNPJ
    tests:
      - dbt_expectations.expect_column_values_to_match_regex:
          regex: "^[0-9.\\/\\-]+$"
          mostly: 0.9   # tolera ~10% de dados sujos na fonte

  - name: data_empenho        # data razoável
    tests:
      - dbt_expectations.expect_column_values_to_be_between:
          min_value: "'2010-01-01'::date"
          max_value: "'2040-12-31'::date"
          row_condition: "data_empenho is not null"
```

### Testes de volume de tabela (em `models:`)

```yaml
models:
  - name: fct_despesas
    tests:
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
```

### Unit tests (OBRIGATÓRIO para todos os models e marts)

Todo model em `marts/` ou `marts/metrics/` **deve obrigatoriamente incluir ao menos um `unit_test`** no seu respectivo `_<model>.yml`.
O `unit_test` valida a lógica de agregação, filtros, categorizações e invariantes fiscais injetando dados sintéticos controlados.

```yaml
unit_tests:
  - name: test_empenhado_liquido_calculo
    model: fct_despesas
    given:
      - input: ref('int_despesas_consolidadas')
        rows:
          - {empenho_id: "1", tipo_empenho: "OR", empenhado: 1000.00}
          - {empenho_id: "1", tipo_empenho: "AN", empenhado: -200.00}
    expect:
      rows:
        - {empenho_id: "1", empenhado_liquido: 800.00}
```

### Packages necessários (`packages.yml`)

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: ">=1.0.0"
  - package: metaplane/dbt_expectations
    version: ">=0.10.0"
```

Rodar `make dbt/deps` após alterar `packages.yml`.

---

## Arquivos yml — Um por model (sem schema.yml monolítico)

### Contract obrigatório nos marts

Todo model em `marts/` **deve** ter um arquivo yml próprio em `models/marts/_<model>.yml`:

- Um arquivo `.yml` por model (nunca um `schema.yml` monolítico)
- Nomenclatura: `_<model_name>.yml` — ex: `_fct_receitas.yml`, `_dim_credor.yml`

```yaml
version: 2

models:
  - name: fct_receitas
    description: "..."
    config:
      contract:
        enforced: true
    columns:
      - name: receita_id
        data_type: text
        constraints:
          - type: not_null
      - name: portal_slug
        data_type: text
        constraints:
          - type: not_null
      - name: valor
        data_type: numeric
      # ... todas as colunas do model
```

Tipos em contratos: `text`, `integer`, `numeric`, `date`, `boolean`.

---

## Comandos

```bash
make dbt/deps     # instala packages (rodar uma vez ou após alterar packages.yml)
make dbt/seed     # carrega CSVs de seeds
make dbt/run      # executa todos os models
make dbt/run SELECT=staging    # executa subset
make dbt/test     # roda testes de contrato e data
make dbt/debug    # testa conexão
```

O wrapper `scripts/run_dbt.py` parseia `DATABASE_URL` automaticamente — não é necessário configurar variáveis individuais.

---

## Auditoria e Paridade Fiscal (Lições Práticas & Invariantes Contábeis)

### 1. Invariantes Contábeis Rígidos (LRF e MCASP)
- **Hierarquia Orçamentária**: Sempre validar a regra `Empenhado >= Liquidado >= Pago`. Testes no dbt devem incluir `expression_is_true` para impedir inversões contábeis nos marts.
- **Exercício Parcial vs Encerrado**: Alertas de sub-execução orçamentária (ex: meta de 70% de execução anual da Saúde) só fazem sentido para **exercícios encerrados** (`!isCurrentYear`). Em anos parciais (ex: Jan-Jul de 2026), a dotação de 12 meses não deve disparar alertas prematuros de gestão irregular.
- **Restos a Pagar Pendentes (MCASP)**: Saldo pendente (`saldo_restos`) **deve** abater anulações e cancelamentos (`empenhado - pago - valor_anulacoes`). Ignorar anulações inflaciona indevidamente o passivo fiscal pendente.

### 2. Separação Estrita Previdenciária (RPPS vs RGPS / Elemento 13)
- **Elemento 13 (Obrigações Patronais)**: É um elemento genérico que engloba contribuições para o **RPPS** (Previdência Municipal - CAPREM), para o **RGPS** (Previdência Federal - INSS / Receita Federal para comissionados/temporários) e para planos de saúde (CASP).
- **Déficit de Repasse do RPPS (CAPREM)**: É **obrigatório** restringir os cálculos do rombo patronal do CAPREM às obrigações previdenciárias próprias do RPPS (`fornecedor_nome ILIKE '%CAPREM%' OR natureza_despesa ILIKE '%RPPS%'`). Lançamentos devidos ao INSS/Receita Federal constituem dívida com a União (RGPS) e **jamais devem ser somados ao déficit do CAPREM**, sob pena de inflacionar o déficit previdenciário municipal por contaminação de impostos federais.
- **Trava por dbt Unit Tests**: Todos os marts de métricas previdenciárias **devem** conter testes de unidade em seus arquivos `_<model>.yml` injetando linhas sintéticas de INSS para garantir que o pipeline `dbt test` falhe caso ocorra contaminação do RGPS no RPPS.

### 3. Gastos Locais e Concentração de Fornecedores (HHI)
- **Filtro Comercial Estrito**: Cálculo de índice de compras locais e concentração HHI deve filtrar apenas transações comerciais de produtos e serviços (`elemento IN ('30', '36', '39', '52')`).
- **Proibição de Agrupamentos Anuais por `SELECT DISTINCT`**: Nunca agrupar fornecedores via `SELECT DISTINCT` em visões anuais pré-agregadas (`fct_despesas_por_fornecedor`). Isso atrai transações não-comerciais (folha/encargos previdenciários) de credores locais, distorcendo o percentual de gastos locais.

### 4. Protocolo de Auditoria e Paridade
- **Verificação ao Centavo**: Antes de aprovar refatorações de marts, extrair o HTML de Produção via `read_url_content` e comparar cada indicador com o banco local ao centavo.
- **Validação Dupla de Testes**: Após qualquer alteração no dbt, executar `make test` (pytest no backend efêmero) e `pnpm test` (vitest e tipagem no TypeScript) sem exceções.

### 5. Sincronização Obrigatória da Taxonomia MCP e Evals de IA (`codegen:taxonomy`)
- **Atualização da Taxonomia MCP**: Sempre que um novo model dbt mart for criado ou alterado em `elt/transform/models/marts/`, execute obrigatoriamente `pnpm codegen:taxonomy` (ou `python3 scripts/codegen-taxonomy.py`). Isso recompila o dicionário `FISCAL_TAXONOMY` em `apps/web/lib/mcp/transparencia-mcp.ts` diretamente dos metadados YAML do dbt.
- **Atualização de Evals de IA**: Ao criar novos marts ou métricas, adicione 2 a 3 perguntas correspondentes no arquivo `apps/web/lib/evals/benchmark-questions.ts` e valide a acurácia executando `pnpm test`.

### 6. Diretrizes Antialucinação de Fases Fiscais e Telemetria do Assistente AI
- **Diferenciação Estrita de Estágios Fiscais**: O assistente de IA nunca deve justificar discrepâncias entre valores Empenhados, Liquidados e Pagos inventando divisões por secretarias ou rubricas (ex: "Educação Infantil"). A diferença entre Empenhado e Liquidado é a reserva orçamentária ainda não executada; a diferença entre Liquidado e Pago representa restos a pagar ou retenções pendentes de repasse.
- **Valores Acumulados do Exercício**: Todas as métricas monetárias nos marts representam o valor acumulado no exercício (ano) até o momento, NUNCA parcelas mensais isoladas.
- **Distinção entre Consolidado do Domínio vs Subconjuntos Específicos**: Ao comparar números agregados do mart (ex: Total Consolidado do CAPREM/CASP `total_empenhado`) com métricas específicas (ex: Contribuição Patronal `total_empenhado_patronal`), a documentação do mart no YAML do dbt deve explicitar essa diferença de escopo para impedir que o agente de IA trate o total do fundo como se fosse uma única obrigação patronal.
- **Ciclo de Telemetria de Feedback (Telemetry-to-Eval)**: Rastrear avaliações dos cidadãos na UI via evento `ai_feedback` no PostHog (com `score`, `message_id` e `portal_slug`). Perguntas reais que gerem feedback negativo (👎) devem ser convertidas em novos casos de teste no benchmark (`benchmark-questions.ts`).

### 7. DDLs em Post-Hooks, Índices de Expressão e Validação em `test_mode`
- **Funções Imutáveis em Índices (`immutable_unaccent`)**: No PostgreSQL, funções usadas em índices de expressão (como `CREATE INDEX ... (immutable_unaccent(lower(coluna)))`) exigem ser declaradas como `IMMUTABLE`. A função `unaccent` nativa do Postgres é `STABLE` e **não pode** ser usada diretamente em um índice. Sempre utilize o wrapper imutável `immutable_unaccent(text)` (configurado em `dbt_project.yml` no `on-run-start` e nas migrations SQL).
- **Proibição de Bypass Silencioso nos Testes**: Como o dbt compila marts como `view` durante `test_mode: true`, DDLs de `CREATE INDEX` em `post_hook` desativadas por `{% if not var('test_mode', false) %}` nunca rodam durante o `make test`. É **obrigatório** manter testes automatizados no Pytest (`test_index_post_hooks.py`) para validar as DDLs de índices contra tabelas do Postgres, prevenindo falhas de colunas inexistentes ou erros de imutabilidade.


