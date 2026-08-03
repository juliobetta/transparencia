-- Staging: transferencias
-- Casts text → numeric e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'transferencias') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        nullif(trim(mes), '') as mes,
        nullif(trim(entidade_pagadora), '') as entidade_pagadora,
        nullif(trim(entidade_recebedora), '') as entidade_recebedora,
        nullif(replace(repasse, ',', '.'), '')::numeric(15, 2) as repasse,
        nullif(replace(devolucao, ',', '.'), '')::numeric(15, 2) as devolucao
    from source
)

select
    ano,
    empresa_id,
    mes,
    entidade_pagadora,
    entidade_recebedora,
    repasse,
    devolucao
from renamed
