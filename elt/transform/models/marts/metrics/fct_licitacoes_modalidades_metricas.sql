{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', "coalesce(nullif(trim(modalidade), ''), 'outros')"]) }} as modalidade_metricas_id,
    portal_slug,
    ano,
    empresa_id,
    coalesce(nullif(trim(modalidade), ''), 'outros') as modalidade,
    count(*)::integer as quantidade,
    sum(coalesce(valor_contrato, 0))::numeric(15, 2) as valor_total
from {{ ref('fct_contratos') }}
group by
    portal_slug,
    ano,
    empresa_id,
    coalesce(nullif(trim(modalidade), ''), 'outros')

