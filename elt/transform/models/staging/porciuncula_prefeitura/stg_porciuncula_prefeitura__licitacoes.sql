-- Staging: licitacoes
-- Casts text → numeric/date e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'licitacoes') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        numero as licitacao_numero,
        nullif(trim(modalidade), '') as modalidade,
        nullif(trim(objeto), '') as objeto,
        nullif(trim(discr), '') as discriminacao,
        nullif(replace(valor, ',', '.'), '')::numeric(15, 2) as valor,
        nullif(trim(situacao), '') as situacao,
        nullif(data_abertura, '')::date as data_abertura,
        nullif(trim(carona), '') as carona
    from source
)

select
    ano,
    empresa_id,
    licitacao_numero,
    modalidade,
    objeto,
    discriminacao,
    valor,
    situacao,
    data_abertura,
    carona
from renamed
