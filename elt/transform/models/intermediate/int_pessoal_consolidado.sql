-- Intermediário: consolida pessoal de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        proventos,
        categoria_funcional,
        vinculo,
        cargo,
        forma_provimento
    from {{ ref('stg_porciuncula_prefeitura__pessoal') }}
)

select
    portal_slug,
    ano,
    empresa_id,
    proventos,
    categoria_funcional,
    vinculo,
    cargo,
    forma_provimento
from porciuncula
