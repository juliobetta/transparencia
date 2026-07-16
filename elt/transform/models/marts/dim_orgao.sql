-- Dimensão: entidades municipais (prefeitura + fundos) por portal
-- Fonte: seed porciuncula_prefeitura_entities (e futuros seeds de novos portais)

SELECT
    MD5(portal_slug || '|' || empresa_id) AS orgao_id,
    portal_slug,
    empresa_id,
    nome AS orgao_nome
FROM {{ ref('porciuncula_prefeitura_entities') }}
