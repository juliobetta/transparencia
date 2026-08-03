-- Intermediário: consolida receitas de todos os portais e agrega ao grain correto.
-- Para adicionar novo portal: incluir novos CTEs + union all em "combined".
-- Agregação por (portal_slug, tipo_receita, ano, empresa_id, codigo) colapsa linhas
-- com o mesmo código mas fontes STN distintas — padrão do portal que emite múltiplas
-- linhas para o mesmo código quando há mais de uma fonte de recurso envolvida.

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
),

combined as (
    select * from porciuncula_orcamentaria
    union all
    select * from porciuncula_uniao
    union all
    select * from porciuncula_estado
)

select
    portal_slug,
    tipo_receita,
    ano,
    empresa_id,
    codigo,
    max(descricao) as descricao,
    sum(previsao_atualizada) as previsao_atualizada,
    sum(arrecadado_efetivo) as arrecadado_efetivo
from combined
group by portal_slug, tipo_receita, ano, empresa_id, codigo
