{{ config(materialized='table') }}

with despesas_agregadas as (
    select
        portal_slug,
        empresa_id,
        ano,
        coalesce(orgao_codigo, '00') as orgao_codigo,
        coalesce(unidade_codigo, '00') as unidade_codigo,
        coalesce(funcao, '00') as funcao_codigo,
        coalesce(subfuncao, '00') as subfuncao_codigo,
        sum(coalesce(dotacao_atualizada, 0)) as total_dotacao_atualizada,
        sum(coalesce(empenhado_liquido, 0)) as total_empenhado,
        sum(coalesce(liquidado, 0)) as total_liquidado,
        sum(coalesce(pago, 0)) as total_pago
    from {{ ref('fct_despesas') }}
    group by
        portal_slug,
        empresa_id,
        ano,
        coalesce(orgao_codigo, '00'),
        coalesce(unidade_codigo, '00'),
        coalesce(funcao, '00'),
        coalesce(subfuncao, '00')
),

metricas_calculadas as (
    select
        portal_slug,
        empresa_id,
        ano,
        orgao_codigo,
        unidade_codigo,
        funcao_codigo,
        subfuncao_codigo,
        total_dotacao_atualizada::numeric(15, 2) as total_dotacao_atualizada,
        total_empenhado::numeric(15, 2) as total_empenhado,
        total_liquidado::numeric(15, 2) as total_liquidado,
        total_pago::numeric(15, 2) as total_pago,
        (total_dotacao_atualizada - total_empenhado)::numeric(15, 2) as saldo_orcamentario,
        case
            when total_dotacao_atualizada > 0
            then (total_empenhado / total_dotacao_atualizada)::numeric(15, 4)
            else 0::numeric(15, 4)
        end as taxa_execucao
    from despesas_agregadas
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'orgao_codigo', 'unidade_codigo', 'funcao_codigo', 'subfuncao_codigo']) }} as execucao_orcamentaria_id,
    portal_slug,
    empresa_id,
    ano,
    orgao_codigo,
    unidade_codigo,
    funcao_codigo,
    subfuncao_codigo,
    total_dotacao_atualizada,
    total_empenhado,
    total_liquidado,
    total_pago,
    saldo_orcamentario,
    taxa_execucao,
    case
        when total_empenhado = 0 and total_dotacao_atualizada = 0
        then 'N/D'
        when total_dotacao_atualizada = 0 and total_empenhado > 0
        then 'excesso'
        when taxa_execucao < 0.30
        then 'baixa'
        when taxa_execucao > 1.00
        then 'excesso'
        else 'normal'
    end as alerta_execucao
from metricas_calculadas
