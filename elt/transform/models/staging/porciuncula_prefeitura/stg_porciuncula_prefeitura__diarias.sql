-- Staging: diarias
-- Casts text → numeric/date e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'diarias') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        numero as diaria_id,
        nullif(replace(valor, ',', '.'), '')::numeric(15, 2) as valor,
        nullif(trim(favorecido), '') as favorecido,
        nullif(trim(cargo), '') as cargo,
        to_timestamp(nullif(data, ''), 'DD/MM/YYYY HH24:MI:SS')::date as data,
        nullif(trim(unidade), '') as unidade,
        nullif(trim(descricao), '') as descricao
    from source
)

select
    ano,
    empresa_id,
    diaria_id,
    valor,
    favorecido,
    cargo,
    data,
    unidade,
    descricao
from renamed
