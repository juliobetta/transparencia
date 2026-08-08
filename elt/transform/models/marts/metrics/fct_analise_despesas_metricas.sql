{{ config(materialized='table') }}

with despesas_agregadas as (
    select
        portal_slug,
        empresa_id,
        ano,
        coalesce(orgao_codigo, '00') as orgao_codigo,
        coalesce(unidade_codigo, '00') as unidade_codigo,
        coalesce(funcao, '00') as funcao_codigo,
        sum(coalesce(dotacao_atualizada, 0)) as total_dotacao_atualizada,
        sum(coalesce(empenhado_liquido, 0)) as total_empenhado,
        sum(coalesce(liquidado, 0)) as total_liquidado,
        sum(coalesce(pago, 0)) as total_pago
    from {{ ref('fct_despesas') }}
    where fonte = 'exercicio'
    group by
        portal_slug,
        empresa_id,
        ano,
        coalesce(orgao_codigo, '00'),
        coalesce(unidade_codigo, '00'),
        coalesce(funcao, '00')
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'orgao_codigo', 'unidade_codigo', 'funcao_codigo']) }} as analise_despesas_id,
    portal_slug,
    empresa_id,
    ano,
    orgao_codigo,
    unidade_codigo,
    funcao_codigo,
    total_dotacao_atualizada::numeric(15, 2) as total_dotacao_atualizada,
    total_empenhado::numeric(15, 2) as total_empenhado,
    total_liquidado::numeric(15, 2) as total_liquidado,
    total_pago::numeric(15, 2) as total_pago
from despesas_agregadas
