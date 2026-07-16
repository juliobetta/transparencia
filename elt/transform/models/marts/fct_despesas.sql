-- Fato: despesas consolidadas com chaves para dimensões
-- Aplica a regra do Empenho Líquido: soma anulações (tipo_empenho='AN') ao empenhado bruto
-- para evitar distorções na taxa de quitação quando há estornos de fim de exercício.

with despesas as (
    select * from {{ ref('int_despesas_consolidadas') }}
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
        d.*,
        coalesce(a.total_anulado, 0) as valor_anulacoes,
        coalesce(d.empenhado, 0) + coalesce(a.total_anulado, 0) as empenhado_liquido
    from despesas d
    left join anulacoes a
        on d.portal_slug = a.portal_slug
        and d.ano = a.ano
        and d.empresa_id = a.empresa_id
        and d.pk_empenho = a.pk_empenho_pai
    where d.tipo_empenho != 'AN'
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'empenho_id']) }} as despesa_id,

    -- Chaves para dimensões
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'fornecedor_cpf_cnpj']) }} as credor_id,
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id']) }} as orgao_id,
    data_empenho,

    -- Atributos da despesa
    portal_slug,
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
    descricao,

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
