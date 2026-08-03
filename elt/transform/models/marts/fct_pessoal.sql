-- Fato: pessoal consolidado de todos os portais
-- Sem surrogate key: dados de pessoal não possuem identificador único por linha no raw.

with pessoal as (
    select
        portal_slug,
        ano,
        empresa_id,
        proventos,
        categoria_funcional,
        vinculo,
        cargo,
        forma_provimento
    from {{ ref('int_pessoal_consolidado') }}
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
from pessoal
