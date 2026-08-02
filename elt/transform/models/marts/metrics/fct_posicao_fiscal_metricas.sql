{{ config(materialized='table') }}

with metadata_gestao as (
    select
        portal_slug,
        coalesce(max(case when key = 'ano_inicio_gestao_atual' then value::int end), 2025) as ano_inicio_gestao
    from {{ ref('dim_metadata') }}
    group by portal_slug
),

receitas_agregadas as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(coalesce(arrecadado, 0)) as total_arrecadado
    from {{ ref('fct_receitas') }}
    group by portal_slug, empresa_id, ano
),

despesas_correntes_agregadas as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(coalesce(pago, 0)) as despesas_pagas
    from {{ ref('fct_despesas') }}
    where fonte = 'exercicio'
    group by portal_slug, empresa_id, ano
),

restos_pagos_agregados as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(coalesce(pago, 0)) as restos_pagos_no_ano
    from {{ ref('fct_despesas') }}
    where fonte = 'restos_a_pagar'
    group by portal_slug, empresa_id, ano
),

restos_pendentes_agregados as (
    select
        d.portal_slug,
        d.empresa_id,
        d.ano,
        sum(
            case
                when d.ano < coalesce(m.ano_inicio_gestao, 2025)
                then coalesce(d.empenhado, 0) - coalesce(d.pago, 0)
                else 0
            end
        ) as restos_pendentes_adm_anterior,
        sum(
            case
                when d.ano >= coalesce(m.ano_inicio_gestao, 2025)
                then coalesce(d.empenhado, 0) - coalesce(d.pago, 0)
                else 0
            end
        ) as restos_pendentes_adm_atual
    from {{ ref('fct_despesas') }} d
    left join metadata_gestao m
        on d.portal_slug = m.portal_slug
    where d.fonte = 'restos_a_pagar'
    group by d.portal_slug, d.empresa_id, d.ano
),

chaves_base as (
    select portal_slug, empresa_id, ano from receitas_agregadas
    union
    select portal_slug, empresa_id, ano from despesas_correntes_agregadas
    union
    select portal_slug, empresa_id, ano from restos_pagos_agregados
    union
    select portal_slug, empresa_id, ano from restos_pendentes_agregados
)

select
    {{ dbt_utils.generate_surrogate_key(['cb.portal_slug', 'cb.empresa_id', 'cb.ano']) }} as posicao_fiscal_id,
    cb.portal_slug,
    cb.empresa_id,
    cb.ano,
    coalesce(r.total_arrecadado, 0) as total_arrecadado,
    coalesce(dc.despesas_pagas, 0) as despesas_pagas,
    coalesce(rp.restos_pagos_no_ano, 0) as restos_pagos_no_ano,
    coalesce(rp_pend.restos_pendentes_adm_anterior, 0) as restos_pendentes_adm_anterior,
    coalesce(rp_pend.restos_pendentes_adm_atual, 0) as restos_pendentes_adm_atual,
    coalesce(r.total_arrecadado, 0) - (coalesce(dc.despesas_pagas, 0) + coalesce(rp.restos_pagos_no_ano, 0)) as saldo_estimado
from chaves_base cb
left join receitas_agregadas r
    on cb.portal_slug = r.portal_slug
    and cb.empresa_id = r.empresa_id
    and cb.ano = r.ano
left join despesas_correntes_agregadas dc
    on cb.portal_slug = dc.portal_slug
    and cb.empresa_id = dc.empresa_id
    and cb.ano = dc.ano
left join restos_pagos_agregados rp
    on cb.portal_slug = rp.portal_slug
    and cb.empresa_id = rp.empresa_id
    and cb.ano = rp.ano
left join restos_pendentes_agregados rp_pend
    on cb.portal_slug = rp_pend.portal_slug
    and cb.empresa_id = rp_pend.empresa_id
    and cb.ano = rp_pend.ano
