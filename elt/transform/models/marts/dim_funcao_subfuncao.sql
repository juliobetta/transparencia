-- Dimensão canônica de Funções e Subfunções (Portaria MOG nº 42/1999)
-- Fonte: seed_funcao_subfuncao

select
    funcao_subfuncao_codigo::text as funcao_subfuncao_codigo,
    funcao_codigo::text as funcao_codigo,
    funcao_nome::text as funcao_nome,
    subfuncao_codigo::text as subfuncao_codigo,
    subfuncao_nome::text as subfuncao_nome
from {{ ref('seed_funcao_subfuncao') }}
