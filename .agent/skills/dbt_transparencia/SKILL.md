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

### Unit tests (quando necessário)

Use `unit_tests:` no mesmo `_<model>.yml` para testar lógica de transformação não-trivial (cálculos, deduplicações, unions com casos especiais). Não escreva unit tests para modelos que apenas renomeiam colunas.

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
