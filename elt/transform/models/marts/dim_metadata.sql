select
    portal_slug,
    key,
    value
from {{ source('raw_porciuncula_prefeitura', 'metadata') }}
