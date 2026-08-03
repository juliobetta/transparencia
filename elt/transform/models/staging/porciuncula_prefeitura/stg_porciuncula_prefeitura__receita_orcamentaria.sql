-- Staging: receita_orcamentaria
-- Casts text → numeric e padroniza nomes de colunas. Relação 1:1 com a fonte.
-- Deduplicação de linhas com mesmo código mas fontes STN distintas ocorre em
-- int_receitas_consolidadas (camada intermediária), conforme boas práticas dbt.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'receita_orcamentaria') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        codigo,
        nullif(trim(coalesce(nome, especificacao)), '') as descricao,
        nullif(replace(replace(coalesce(previsao_atualizada, prev_atualizada), '.', ''), ',', '.'), '')::numeric(15, 2) as previsao_atualizada,
        nullif(replace(replace(coalesce(arrecadado_total, arrec_total), '.', ''), ',', '.'), '')::numeric(15, 2) as arrecadado_efetivo
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
