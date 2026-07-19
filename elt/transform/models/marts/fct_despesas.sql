-- Fato: despesas consolidadas com chaves para dimensões
-- Aplica a regra do Empenho Líquido: soma anulações (tipo_empenho='AN') ao empenhado bruto
-- para evitar distorções na taxa de quitação quando há estornos de fim de exercício.
-- RAP (restos a pagar): tipo_empenho é null — incluídos na tabela final sem anulações.

with despesas as (
    select
        portal_slug,
        fonte,
        ano,
        empresa_id,
        empenho_id,
        pk_empenho,
        pk_empenho_pai,
        tipo_empenho,
        orgao_codigo,
        funcao,
        funcao_nome,
        subfuncao,
        subfuncao_nome,
        elemento,
        natureza_despesa,
        categoria,
        grupo_natureza,
        modalidade,
        programa,
        programa_nome,
        proj_atividade,
        projeto_atividade_nome,
        mes,
        fornecedor_nome,
        fornecedor_cpf_cnpj,
        fornecedor_raw,
        licitacao_numero,
        licitacao_modalidade,
        licitacao_descricao,
        fongrupo,
        fongrupo_desc,
        foncodigo,
        foncodigo_desc,
        fonro,
        fonro_desc,
        fonte_stn,
        fonte_stn_desc,
        fonte_recurso_desc,
        data_empenho,
        empenhado,
        liquidado,
        pago,
        dotacao_inicial,
        alteracao_dotacao,
        dotacao_atualizada,
        anulado,
        reforco,
        descricao,
        entidade_nome,
        proc,
        codlo,
        cfpro,
        ficha,
        codif,
        codigo,
        produ,
        vingrupo_vincodigo,
        vincodigonome
    from {{ ref('int_despesas_consolidadas') }}
),

-- Agrega anulações por empenho pai para calcular empenho líquido
anulacoes as (
    select
        portal_slug,
        ano,
        empresa_id,
        pk_empenho_pai,
        sum(coalesce(empenhado, 0)) as total_anulado
    from despesas
    where tipo_empenho = 'AN'
    group by portal_slug, ano, empresa_id, pk_empenho_pai
),

empenhos as (
    select
        d.portal_slug,
        d.fonte,
        d.ano,
        d.empresa_id,
        d.empenho_id,
        d.pk_empenho,
        d.pk_empenho_pai,
        d.tipo_empenho,
        d.orgao_codigo,
        d.funcao,
        d.funcao_nome,
        d.subfuncao,
        d.subfuncao_nome,
        d.elemento,
        d.natureza_despesa,
        d.categoria,
        d.grupo_natureza,
        d.modalidade,
        d.programa,
        d.programa_nome,
        d.proj_atividade,
        d.projeto_atividade_nome,
        d.mes,
        d.fornecedor_nome,
        d.fornecedor_cpf_cnpj,
        d.fornecedor_raw,
        d.licitacao_numero,
        d.licitacao_modalidade,
        d.licitacao_descricao,
        d.fongrupo,
        d.fongrupo_desc,
        d.foncodigo,
        d.foncodigo_desc,
        d.fonro,
        d.fonro_desc,
        d.fonte_stn,
        d.fonte_stn_desc,
        d.fonte_recurso_desc,
        d.data_empenho,
        d.empenhado,
        d.liquidado,
        d.pago,
        d.dotacao_inicial,
        d.alteracao_dotacao,
        d.dotacao_atualizada,
        d.anulado,
        d.reforco,
        d.descricao,
        d.entidade_nome,
        d.proc,
        d.codlo,
        d.cfpro,
        d.ficha,
        d.codif,
        d.codigo,
        d.produ,
        d.vingrupo_vincodigo,
        d.vincodigonome,
        coalesce(a.total_anulado, 0) as valor_anulacoes,
        coalesce(d.empenhado, 0) + coalesce(a.total_anulado, 0) as empenhado_liquido
    from despesas d
    left join anulacoes a
        on d.portal_slug = a.portal_slug
        and d.ano = a.ano
        and d.empresa_id = a.empresa_id
        and d.pk_empenho = a.pk_empenho_pai
    where d.tipo_empenho != 'AN' or d.tipo_empenho is null
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'fonte', 'ano', 'empresa_id', 'empenho_id']) }} as despesa_id,

    -- Chaves para dimensões
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'fornecedor_cpf_cnpj']) }} as credor_id,
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id']) }} as orgao_id,
    data_empenho,

    -- Atributos da despesa
    portal_slug,
    fonte,
    ano,
    empresa_id,
    empenho_id,
    pk_empenho,
    tipo_empenho,
    orgao_codigo,
    funcao,
    funcao_nome,
    subfuncao,
    subfuncao_nome,
    elemento,
    natureza_despesa,
    grupo_natureza,
    modalidade,
    programa,
    programa_nome,
    proj_atividade,
    projeto_atividade_nome,
    mes,
    fornecedor_nome,
    fornecedor_cpf_cnpj,
    licitacao_numero,
    licitacao_modalidade,
    fonte_recurso_desc,
    coalesce(produ, descricao) as descricao,

    -- Valores financeiros (Lei de Responsabilidade Fiscal: pago ≤ liquidado ≤ empenhado)
    empenhado,
    empenhado_liquido,
    liquidado,
    pago,
    dotacao_inicial,
    alteracao_dotacao,
    dotacao_atualizada,
    reforco,
    valor_anulacoes

from empenhos
