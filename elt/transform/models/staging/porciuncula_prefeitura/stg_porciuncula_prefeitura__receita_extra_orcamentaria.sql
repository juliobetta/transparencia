-- Staging: receita_extra_orcamentaria
-- Casts text → numeric, padroniza nomes de colunas e inclui portal_slug. Relação 1:1 com a fonte.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'receita_extra_orcamentaria') }}
),

renamed as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano::int as ano,
        empresa as empresa_id,
        codigo,
        nullif(trim(descricao), '') as descricao,
        case
            when valor is null then 0.00
            when valor ~ '^[0-9]+(\.[0-9]+)?$' then valor::numeric(15, 2)
            else nullif(replace(replace(valor, '.', ''), ',', '.'), '')::numeric(15, 2)
        end as valor_arrecadado,
        nullif(trim(dtlan), '') as data_lancamento,
        nullif(trim(empresanome), '') as empresa_nome
    from source
)

select
    portal_slug,
    ano,
    empresa_id,
    codigo,
    descricao,
    valor_arrecadado,
    data_lancamento,
    empresa_nome
from renamed
