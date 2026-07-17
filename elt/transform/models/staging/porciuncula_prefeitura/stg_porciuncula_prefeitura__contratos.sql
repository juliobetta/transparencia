-- Staging: contratos
-- Casts text → numeric e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'contratos') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        numero as contrato_numero,
        nullif(trim(fornecedor), '') as fornecedor_nome,
        nullif(trim(objeto), '') as objeto,
        nullif(replace(valcon, ',', '.'), '')::numeric(15, 2) as valor_contrato,
        nullif(trim(licitacao_numero), '') as licitacao_numero,
        nullif(trim(modali), '') as modalidade,
        nullif(trim(mes), '') as mes,
        nullif(trim(tipocoobra), '') as tipo_obra,
        nullif(trim(numobra), '') as numero_obra,
        nullif(replace(empenhado, ',', '.'), '')::numeric(15, 2) as empenhado
    from source
)

select
    ano,
    empresa_id,
    contrato_numero,
    fornecedor_nome,
    objeto,
    valor_contrato,
    licitacao_numero,
    modalidade,
    mes,
    tipo_obra,
    numero_obra,
    empenhado
from renamed
