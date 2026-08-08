{{ config(materialized='table') }}

with diarias_detalhadas as (
    select
        portal_slug,
        empresa_id,
        ano,
        coalesce(favorecido, 'OUTROS') as favorecido,
        coalesce(cargo, 'NÃO INFORMADO') as cargo,
        sum(coalesce(valor, 0)) as total_valor,
        count(*) as qtd_concessoes
    from {{ ref('fct_diarias') }}
    group by
        portal_slug,
        empresa_id,
        ano,
        coalesce(favorecido, 'OUTROS'),
        coalesce(cargo, 'NÃO INFORMADO')
),

diarias_totais as (
    select
        portal_slug,
        empresa_id,
        ano,
        '__TOTAL__' as favorecido,
        '__TOTAL__' as cargo,
        sum(total_valor) as total_valor,
        sum(qtd_concessoes) as qtd_concessoes
    from diarias_detalhadas
    group by portal_slug, empresa_id, ano
),

uniao as (
    select * from diarias_detalhadas
    union all
    select * from diarias_totais
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'favorecido', 'cargo']) }} as diarias_metricas_id,
    portal_slug,
    empresa_id,
    ano,
    favorecido,
    cargo,
    total_valor::numeric(15, 2) as total_valor,
    qtd_concessoes::integer as qtd_concessoes
from uniao
