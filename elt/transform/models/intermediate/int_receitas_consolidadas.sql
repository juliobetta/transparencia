-- Intermediário: consolida receitas de todos os portais via union all.
-- Para adicionar novo portal: incluir novos CTEs + union all abaixo.
-- Deduplicação intraorçamentária (prefixos 17%, 27%) ocorre em fct_receitas via tipo_receita.

with porciuncula_orcamentaria as (
    select
        'porciuncula_prefeitura' as portal_slug,
        'orcamentaria' as tipo_receita,
        ano,
        empresa_id,
        codigo,
        descricao,
        previsao_atualizada,
        arrecadado_efetivo
    from {{ ref('stg_porciuncula_prefeitura__receita_orcamentaria') }}
),

porciuncula_uniao as (
    select
        'porciuncula_prefeitura' as portal_slug,
        'uniao' as tipo_receita,
        ano,
        empresa_id,
        codigo,
        descricao,
        previsao_atualizada,
        arrecadado_efetivo
    from {{ ref('stg_porciuncula_prefeitura__receita_uniao') }}
),

porciuncula_estado as (
    select
        'porciuncula_prefeitura' as portal_slug,
        'estado' as tipo_receita,
        ano,
        empresa_id,
        codigo,
        descricao,
        previsao_atualizada,
        arrecadado_efetivo
    from {{ ref('stg_porciuncula_prefeitura__receita_estado') }}
)

select
    portal_slug,
    tipo_receita,
    ano,
    empresa_id,
    codigo,
    descricao,
    previsao_atualizada,
    arrecadado_efetivo
from porciuncula_orcamentaria
union all
select
    portal_slug,
    tipo_receita,
    ano,
    empresa_id,
    codigo,
    descricao,
    previsao_atualizada,
    arrecadado_efetivo
from porciuncula_uniao
union all
select
    portal_slug,
    tipo_receita,
    ano,
    empresa_id,
    codigo,
    descricao,
    previsao_atualizada,
    arrecadado_efetivo
from porciuncula_estado
