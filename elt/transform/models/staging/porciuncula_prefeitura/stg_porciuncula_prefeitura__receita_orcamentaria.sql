-- Staging: receita_orcamentaria
-- Casts text → numeric e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'receita_orcamentaria') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        codigo,
        nullif(trim(descricao), '') as descricao,
        nullif(replace(previsao_atualizada, ',', '.'), '')::numeric(15, 2) as previsao_atualizada,
        coalesce(
            nullif(replace(arrecadado_total, ',', '.'), '')::numeric(15, 2),
            nullif(replace(arrecadado, ',', '.'), '')::numeric(15, 2)
        ) as arrecadado_efetivo
    from source
)

select
    ano,
    empresa_id,
    codigo,
    descricao,
    previsao_atualizada,
    arrecadado_efetivo
from renamed
