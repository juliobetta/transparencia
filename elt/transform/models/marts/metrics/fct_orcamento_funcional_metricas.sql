{{ config(materialized='table') }}

with despesas_funcionais as (
    select
        portal_slug,
        empresa_id,
        ano,
        coalesce(funcao_nome, 'Sem função') as funcao_nome,
        coalesce(subfuncao_nome, 'Sem subfunção') as subfuncao_nome,
        coalesce(sum(dotacao_atualizada), 0) as dotacao_atualizada,
        coalesce(sum(empenhado), 0) as empenhado,
        coalesce(sum(liquidado), 0) as liquidado,
        coalesce(sum(pago), 0) as pago
    from {{ ref('fct_despesas') }}
    where ano is not null
    group by
        portal_slug,
        empresa_id,
        ano,
        funcao_nome,
        subfuncao_nome
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'funcao_nome', 'subfuncao_nome']) }} as orcamento_funcional_id,
    portal_slug,
    empresa_id,
    ano,
    funcao_nome,
    subfuncao_nome,
    dotacao_atualizada::numeric(15, 2) as dotacao_atualizada,
    empenhado::numeric(15, 2) as empenhado,
    liquidado::numeric(15, 2) as liquidado,
    pago::numeric(15, 2) as pago
from despesas_funcionais
