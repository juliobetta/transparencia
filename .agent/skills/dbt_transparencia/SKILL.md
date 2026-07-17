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

## Contract Obrigatório nos Marts

Todo arquivo em `marts/` **deve** ter entrada correspondente em `models/marts/schema.yml`:

```yaml
- name: dim_licitacao
  config:
    contract:
      enforced: true
  columns:
    - name: licitacao_id
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

Tipos em `schema.yml`: `text`, `integer`, `numeric`, `date`, `boolean`.

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
