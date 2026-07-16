-- Intermediário: consolida despesas de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        *
    from {{ ref('stg_porciuncula_prefeitura__despesas_gerais') }}
)

select * from porciuncula
