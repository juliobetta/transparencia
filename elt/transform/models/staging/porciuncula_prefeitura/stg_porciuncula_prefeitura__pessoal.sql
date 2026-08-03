-- Staging: pessoal
-- Casts text → numeric e padroniza nomes de colunas.
-- proventos: formato BR com ponto de milhar e vírgula decimal → remove ponto, depois substitui vírgula

with source as (
    select * from {{ source('porciuncula_prefeitura', 'pessoal') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        nullif(replace(replace(proventos, '.', ''), ',', '.'), '')::numeric(15, 2) as proventos,
        nullif(trim(categoriafuncional), '') as categoria_funcional,
        nullif(trim(vinculo), '') as vinculo,
        nullif(trim(cargo), '') as cargo,
        nullif(trim(formaprovimento), '') as forma_provimento
    from source
)

select
    ano,
    empresa_id,
    proventos,
    categoria_funcional,
    vinculo,
    cargo,
    forma_provimento
from renamed
