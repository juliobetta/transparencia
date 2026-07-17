select
    portal_slug,
    key,
    value
from {{ source('porciuncula_prefeitura', 'metadata') }}
