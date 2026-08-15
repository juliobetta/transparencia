

with tendencias as (
    select
        d.portal_slug,
        d.ano,
        sum(case when d.elemento = '97' then coalesce(d.empenhado_liquido, 0) else 0 end) as aporte_exigido,
        sum(case when d.elemento = '97' then coalesce(d.pago, 0) else 0 end) as aporte_quitado,
        sum(case when d.elemento = '71' then coalesce(d.pago, 0) else 0 end) as amortizacao_divida
    from {{ ref('fct_despesas') }} d
    where
        d.fonte = 'exercicio'
        and d.elemento in ('97', '71')
        and (d.tipo_empenho is null or d.tipo_empenho != 'AN')
    group by d.portal_slug, d.ano
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano']) }} as caprem_tendencia_id,
    portal_slug,
    ano,
    aporte_exigido::numeric(15, 2) as aporte_exigido,
    aporte_quitado::numeric(15, 2) as aporte_quitado,
    case
        when aporte_exigido > 0 then (aporte_quitado / aporte_exigido) * 100
        else 100
    end::numeric(15, 2) as taxa_adimplencia,
    amortizacao_divida::numeric(15, 2) as amortizacao_divida
from tendencias
