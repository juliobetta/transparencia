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
        nullif(trim(licit), '') as modalidade,
        nullif(trim(discr), '') as objeto,
        nullif(trim(discr10), '') as discriminacao,
        nullif(replace(valor, ',', '.'), '')::numeric(15, 2) as valor,
        nullif(trim(situacao), '') as situacao,
        case when nullif(trim(datae), '') is not null then to_date(left(trim(datae), 10), 'DD/MM/YYYY') end as data_abertura,
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
