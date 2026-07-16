-- Staging: despesas_gerais
-- Casts text → numeric/date e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'despesas_gerais') }}
),

renamed as (
    select
        -- Chaves
        ano::int as ano,
        empresa as empresa_id,
        numero as empenho_id,
        pkemp as pk_empenho,
        pkempa as pk_empenho_pai,

        -- Classificação orçamentária
        tpem as tipo_empenho,
        orgao as orgao_codigo,
        funcao,
        funcaonome as funcao_nome,
        subfuncao,
        subfuncaonome as subfuncao_nome,
        elemento,
        natureza as natureza_despesa,
        categoria,
        gruponatureza as grupo_natureza,
        modalidade,
        programa,
        programanome as programa_nome,
        projativ as proj_atividade,
        projeto_atividade_nome,
        mes,

        -- Fornecedor
        nomefor as fornecedor_nome,
        cpfformatado as fornecedor_cpf_cnpj,
        fornecedor as fornecedor_raw,

        -- Licitação
        numlicit as licitacao_numero,
        licit as licitacao_modalidade,
        desclicit_detalhesempenho as licitacao_descricao,

        -- Fonte de recurso
        fongrupo,
        fongrupodesc as fongrupo_desc,
        foncodigo,
        foncodigodesc as foncodigo_desc,
        fonro,
        fonrodesc as fonro_desc,
        fonte_stn,
        fonte_stndesc as fonte_stn_desc,
        descfonrec as fonte_recurso_desc,

        -- Datas
        nullif(data_empenho, '')::date as data_empenho,

        -- Valores financeiros (R$)
        -- Formato raw: vírgula decimal (ex: "1234,56") → substitui por ponto antes do cast
        nullif(replace(empenhado, ',', '.'), '')::numeric(15, 2) as empenhado,
        nullif(replace(liquidado, ',', '.'), '')::numeric(15, 2) as liquidado,
        nullif(replace(pago, ',', '.'), '')::numeric(15, 2) as pago,
        nullif(replace(dotac, ',', '.'), '')::numeric(15, 2) as dotacao_inicial,
        nullif(replace(altdo, ',', '.'), '')::numeric(15, 2) as alteracao_dotacao,
        nullif(replace(dotacatualizada, ',', '.'), '')::numeric(15, 2) as dotacao_atualizada,
        nullif(replace(anulado, ',', '.'), '')::numeric(15, 2) as anulado,
        nullif(replace(reforco, ',', '.'), '')::numeric(15, 2) as reforco,

        -- Campos complementares
        descricao,
        nomeempresa as entidade_nome,
        proc,
        codlo,
        cfpro,
        ficha,
        codif,
        codigo,
        produ,
        vingrupo_vincodigo,
        vincodigonome
    from source
)

select * from renamed
