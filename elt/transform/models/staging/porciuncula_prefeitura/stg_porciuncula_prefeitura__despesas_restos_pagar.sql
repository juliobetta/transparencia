-- Staging: despesas_restos_pagar
-- Casts text → numeric e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'despesas_restos_pagar') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        numero as rap_id,
        descricao,
        nullif(replace(empenhado, ',', '.'), '')::numeric(15, 2) as empenhado,
        nullif(replace(pago, ',', '.'), '')::numeric(15, 2) as pago
    from source
)

select
    ano,
    empresa_id,
    rap_id,
    descricao,
    empenhado,
    pago
from renamed
