-- Fato: despesas consolidadas com chaves para dimensões
-- Aplica a regra do Empenho Líquido: soma anulações (tipo_empenho='AN') ao empenhado bruto
-- para evitar distorções na taxa de quitação quando há estornos de fim de exercício.

WITH despesas AS (
    SELECT * FROM {{ ref('int_despesas_consolidadas') }}
),

-- Agrega anulações por empenho pai para calcular empenho líquido
anulacoes AS (
    SELECT
        portal_slug,
        ano,
        empresa_id,
        pk_empenho_pai,
        SUM(COALESCE(empenhado, 0)) AS total_anulado
    FROM despesas
    WHERE tipo_empenho = 'AN'
    GROUP BY portal_slug, ano, empresa_id, pk_empenho_pai
),

empenhos AS (
    SELECT
        d.*,
        COALESCE(a.total_anulado, 0) AS valor_anulacoes,
        COALESCE(d.empenhado, 0) + COALESCE(a.total_anulado, 0) AS empenhado_liquido
    FROM despesas d
    LEFT JOIN anulacoes a
        ON d.portal_slug = a.portal_slug
        AND d.ano = a.ano
        AND d.empresa_id = a.empresa_id
        AND d.pk_empenho = a.pk_empenho_pai
    WHERE d.tipo_empenho != 'AN'
)

SELECT
    MD5(
        COALESCE(e.portal_slug, '') || '|' ||
        COALESCE(e.ano::TEXT, '') || '|' ||
        COALESCE(e.empresa_id, '') || '|' ||
        COALESCE(e.empenho_id, '')
    ) AS despesa_id,

    -- Chaves para dimensões
    MD5(COALESCE(e.portal_slug, '') || '|' || COALESCE(e.fornecedor_cpf_cnpj, '')) AS credor_id,
    MD5(e.portal_slug || '|' || e.empresa_id) AS orgao_id,
    e.data_empenho,

    -- Atributos da despesa
    e.portal_slug,
    e.ano,
    e.empresa_id,
    e.empenho_id,
    e.pk_empenho,
    e.tipo_empenho,
    e.orgao_codigo,
    e.funcao,
    e.funcao_nome,
    e.subfuncao,
    e.subfuncao_nome,
    e.elemento,
    e.natureza_despesa,
    e.grupo_natureza,
    e.modalidade,
    e.programa,
    e.programa_nome,
    e.proj_atividade,
    e.projeto_atividade_nome,
    e.mes,
    e.fornecedor_nome,
    e.fornecedor_cpf_cnpj,
    e.licitacao_numero,
    e.licitacao_modalidade,
    e.fonte_recurso_desc,
    e.descricao,

    -- Valores financeiros (Lei de Responsabilidade Fiscal: Pago ≤ Liquidado ≤ Empenhado)
    e.empenhado,
    e.empenhado_liquido,
    e.liquidado,
    e.pago,
    e.dotacao_inicial,
    e.alteracao_dotacao,
    e.dotacao_atualizada,
    e.reforco,
    e.valor_anulacoes

FROM empenhos e
