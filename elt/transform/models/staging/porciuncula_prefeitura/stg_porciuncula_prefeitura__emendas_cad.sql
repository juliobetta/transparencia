-- Staging: emendas_cad
-- Casts text → numeric e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'emendas_cad') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        nullif(trim(numero_emenda), '') as numero_emenda,
        nullif(trim(resumo), '') as resumo,
        nullif(replace(valor_total, ',', '.'), '')::numeric(15, 2) as valor_total,
        nullif(replace(empenhado, ',', '.'), '')::numeric(15, 2) as empenhado,
        nullif(trim(autor), '') as autor,
        nullif(trim(tipo_emenda_descr), '') as tipo_emenda,
        nullif(trim(esfera_origem), '') as esfera_origem,
        nullif(trim(ato_normativo), '') as ato_normativo,
        nullif(trim(destinacao_descr), '') as destinacao
    from source
)

select
    ano,
    empresa_id,
    numero_emenda,
    resumo,
    valor_total,
    empenhado,
    autor,
    tipo_emenda,
    esfera_origem,
    ato_normativo,
    destinacao
from renamed
