

with restos_com_origem as (
    select
        f.portal_slug,
        f.empresa_id,
        f.ano,
        coalesce(
            g.ano,
            f.ano
        ) as ano_origem,
        coalesce(f.empenhado, 0) as empenhado,
        coalesce(f.pago, 0) as pago,
        coalesce(f.valor_anulacoes, 0) as valor_anulacoes
    from {{ ref('fct_despesas') }} f
    left join {{ ref('fct_despesas') }} g
        on f.empenho_id = g.empenho_id
       and f.empresa_id = g.empresa_id
       and g.fonte = 'exercicio'
       and g.portal_slug = f.portal_slug
    where f.fonte = 'restos_a_pagar'
),

restos_agregados as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(empenhado) as restos_inscritos,
        sum(pago) as restos_pagos,
        sum(valor_anulacoes) as restos_cancelados,
        min(case when (empenhado - pago) > 0 then ano_origem else ano end) as divida_mais_antiga_ano
    from restos_com_origem
    group by
        portal_slug,
        empresa_id,
        ano
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano']) }} as restos_metricas_id,
    portal_slug,
    empresa_id,
    ano,
    restos_inscritos::numeric(15, 2) as restos_inscritos,
    restos_pagos::numeric(15, 2) as restos_pagos,
    restos_cancelados::numeric(15, 2) as restos_cancelados,
    (restos_inscritos - restos_pagos)::numeric(15, 2) as saldo_restos,
    coalesce(divida_mais_antiga_ano, ano)::integer as divida_mais_antiga_ano
from restos_agregados
