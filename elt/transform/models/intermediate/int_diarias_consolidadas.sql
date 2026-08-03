-- Intermediário: consolida diarias de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        diaria_id,
        valor,
        favorecido,
        cargo,
        data,
        unidade,
        descricao
    from {{ ref('stg_porciuncula_prefeitura__diarias') }}
)

select
    portal_slug,
    ano,
    empresa_id,
    diaria_id,
    valor,
    favorecido,
    cargo,
    data,
    unidade,
    descricao
from porciuncula
