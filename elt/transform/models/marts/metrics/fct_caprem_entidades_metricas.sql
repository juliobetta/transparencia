{{ config(materialized='table') }}

with caprem_entidades as (
    select
        f.portal_slug,
        f.ano,
        coalesce(o.orgao_nome, f.empresa_id) as entidade,
        sum(coalesce(f.empenhado_liquido, 0)) as empenhado,
        sum(coalesce(f.liquidado, 0)) as liquidado,
        sum(coalesce(f.pago, 0)) as pago
    from {{ ref('fct_despesas') }} f
    left join {{ ref('dim_orgao') }} o
        on o.empresa_id = f.empresa_id
        and o.portal_slug = f.portal_slug
    where
        f.fonte = 'exercicio'
        and (
            f.elemento in ('13', '71', '97')
            or f.orgao_codigo = '1061'
            or f.credor_id = '1061'
            or f.fornecedor_nome ilike '%CAPREM%'
            or f.fornecedor_nome ilike '%CASP%'
            or f.fornecedor_cpf_cnpj = '07.573.075/0001-00'
            or f.descricao ilike '%CAPREM%'
            or f.descricao ilike '%CASP%'
        )
        and (f.tipo_empenho is null or f.tipo_empenho != 'AN')
    group by
        f.portal_slug,
        f.ano,
        coalesce(o.orgao_nome, f.empresa_id)
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'entidade']) }} as caprem_entidade_id,
    portal_slug,
    ano,
    entidade,
    empenhado::numeric(15, 2) as empenhado,
    liquidado::numeric(15, 2) as liquidado,
    pago::numeric(15, 2) as pago,
    case
        when empenhado > 0 then (pago / empenhado) * 100
        else 0
    end::numeric(15, 2) as taxa_execucao
from caprem_entidades
