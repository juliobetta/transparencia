-- Intermediário: consolida emendas de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        numero_emenda,
        resumo,
        valor_total,
        empenhado,
        autor,
        tipo_emenda,
        esfera_origem,
        ato_normativo,
        destinacao
    from {{ ref('stg_porciuncula_prefeitura__emendas_cad') }}
)

select
    portal_slug,
    ano,
    empresa_id,
    numero_emenda,
    resumo,
    valor_total,
    empenhado,
    autor,
    tipo_emenda,
    esfera_origem,
    ato_normativo,
    destinacao
from porciuncula
