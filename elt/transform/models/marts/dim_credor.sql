-- Dimensão: credores/fornecedores únicos por portal

WITH base AS (
    SELECT
        portal_slug,
        fornecedor_cpf_cnpj,
        fornecedor_nome,
        COUNT(*) AS total_empenhos
    FROM {{ ref('int_despesas_consolidadas') }}
    WHERE fornecedor_nome IS NOT NULL
    GROUP BY portal_slug, fornecedor_cpf_cnpj, fornecedor_nome
),

deduplicado AS (
    -- Mantém a ocorrência mais frequente do nome para cada CPF/CNPJ
    SELECT DISTINCT ON (portal_slug, fornecedor_cpf_cnpj)
        portal_slug,
        fornecedor_cpf_cnpj,
        fornecedor_nome
    FROM base
    ORDER BY portal_slug, fornecedor_cpf_cnpj, total_empenhos DESC
)

SELECT
    MD5(COALESCE(portal_slug, '') || '|' || COALESCE(fornecedor_cpf_cnpj, '')) AS credor_id,
    portal_slug,
    fornecedor_cpf_cnpj,
    fornecedor_nome
FROM deduplicado
