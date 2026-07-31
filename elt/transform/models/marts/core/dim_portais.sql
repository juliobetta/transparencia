with portais as (
    select * from {{ ref('seed_portais') }}
),

max_extracao as (
    select
        portal_slug,
        max(data_empenho) as ultima_transacao
    from {{ ref('fct_despesas') }}
    group by portal_slug
)

select
    p.portal_slug,
    p.display_name,
    p.uf,
    p.portal_url,
    p.base_host,
    p.cidade_clean,
    p.ano_inicial,
    p.empresa_padrao,
    p.brasao_asset,
    coalesce(m.ultima_transacao, current_date) as data_extracao
from portais p
left join max_extracao m on p.portal_slug = m.portal_slug
