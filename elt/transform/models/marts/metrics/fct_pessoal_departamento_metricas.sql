

select
    {{ dbt_utils.generate_surrogate_key(["'porciuncula_prefeitura'", 'ano', "coalesce(nullif(ltrim(empresa, '0'), ''), '0')", 'descricao']) }} as departamento_metricas_id,
    'porciuncula_prefeitura' as portal_slug,
    ano,
    coalesce(nullif(ltrim(empresa, '0'), ''), '0') as empresa_id,
    descricao,
    sum(coalesce(pago, 0))::numeric(15, 2) as total_pago
from {{ ref('fct_despesas_por_fornecedor') }}
where
    descricao ~* ' E OUT(ROS?|\.)'
    or descricao ilike '%E OUTROS%'
    or descricao ilike '%E OUTRO%'
group by
    ano,
    coalesce(nullif(ltrim(empresa, '0'), ''), '0'),
    descricao

