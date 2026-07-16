-- Intermediário: consolida despesas de todos os portais via UNION ALL.
-- Para adicionar novo portal: incluir novo CTE + UNION ALL abaixo.

WITH porciuncula AS (
    SELECT
        'porciuncula_prefeitura' AS portal_slug,
        *
    FROM {{ ref('stg_porciuncula_prefeitura__despesas_gerais') }}
)

SELECT * FROM porciuncula
