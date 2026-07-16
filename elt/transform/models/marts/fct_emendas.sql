-- Fato: emendas consolidadas de todos os portais

with emendas as (
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
    from {{ ref('int_emendas_consolidadas') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'numero_emenda']) }} as emenda_id,
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
from emendas
