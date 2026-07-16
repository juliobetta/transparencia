-- Staging: despesas_gerais
-- Casts TEXT → NUMERIC/DATE e padroniza nomes de colunas.

WITH source AS (
    SELECT * FROM {{ source('porciuncula_prefeitura', 'despesas_gerais') }}
),

renamed AS (
    SELECT
        -- Chaves
        ano::INT AS ano,
        empresa AS empresa_id,
        numero AS empenho_id,
        pkemp AS pk_empenho,
        pkempa AS pk_empenho_pai,

        -- Classificação orçamentária
        tpem AS tipo_empenho,
        orgao AS orgao_codigo,
        funcao,
        funcaonome AS funcao_nome,
        subfuncao,
        subfuncaonome AS subfuncao_nome,
        elemento,
        natureza AS natureza_despesa,
        categoria,
        gruponatureza AS grupo_natureza,
        modalidade,
        programa,
        programanome AS programa_nome,
        projativ AS proj_atividade,
        projeto_atividade_nome,
        mes,

        -- Fornecedor
        nomefor AS fornecedor_nome,
        cpfformatado AS fornecedor_cpf_cnpj,
        fornecedor AS fornecedor_raw,

        -- Licitação
        numlicit AS licitacao_numero,
        licit AS licitacao_modalidade,
        desclicit_detalhesempenho AS licitacao_descricao,

        -- Fonte de recurso
        fongrupo,
        fongrupodesc AS fongrupo_desc,
        foncodigo,
        foncodigodesc AS foncodigo_desc,
        fonro,
        fonrodesc AS fonro_desc,
        fonte_stn,
        fonte_stndesc AS fonte_stn_desc,
        descfonrec AS fonte_recurso_desc,

        -- Datas
        NULLIF(data_empenho, '')::DATE AS data_empenho,

        -- Valores financeiros (R$)
        -- Formato raw: vírgula decimal (ex: "1234,56") → substitui por ponto antes do cast
        NULLIF(REPLACE(empenhado, ',', '.'), '')::NUMERIC(15, 2) AS empenhado,
        NULLIF(REPLACE(liquidado, ',', '.'), '')::NUMERIC(15, 2) AS liquidado,
        NULLIF(REPLACE(pago, ',', '.'), '')::NUMERIC(15, 2) AS pago,
        NULLIF(REPLACE(dotac, ',', '.'), '')::NUMERIC(15, 2) AS dotacao_inicial,
        NULLIF(REPLACE(altdo, ',', '.'), '')::NUMERIC(15, 2) AS alteracao_dotacao,
        NULLIF(REPLACE(dotacatualizada, ',', '.'), '')::NUMERIC(15, 2) AS dotacao_atualizada,
        NULLIF(REPLACE(anulado, ',', '.'), '')::NUMERIC(15, 2) AS anulado,
        NULLIF(REPLACE(reforco, ',', '.'), '')::NUMERIC(15, 2) AS reforco,

        -- Campos complementares
        descricao,
        nomeempresa AS entidade_nome,
        proc,
        codlo,
        cfpro,
        ficha,
        codif,
        codigo,
        produ,
        vingrupo_vincodigo,
        vincodigonome
    FROM source
)

SELECT * FROM renamed
