{{ config(
    materialized='table',
    pre_hook="CREATE EXTENSION IF NOT EXISTS unaccent;"
) }}

with licitacoes_proprias as (
    select
        portal_slug,
        ano,
        empresa_id,
        'licitacao_propria' as tipo_contratacao,
        licitacao_numero as numero,
        licitacao_numero,
        null::text as contrato_numero,
        null::text as fornecedor_nome,
        coalesce(discriminacao, licitacao_numero) as objeto,
        coalesce(nullif(trim(modalidade), ''), 'outros') as modalidade,
        null::text as fundlegal,
        carona,
        null::integer as mes,
        null::text as numero_obra,
        null::text as tipo_obra,
        1::integer as quantidade,
        coalesce(valor, 0)::numeric(15, 2) as licitacao_valor,
        0::numeric(15, 2) as valor_contrato,
        0::numeric(15, 2) as empenhado_contrato,
        0::numeric(15, 2) as pago_contrato,
        null::date as data_referencia
    from {{ ref('fct_licitacoes') }}
    where coalesce(carona, 'N') != 'S'
      and lower(unaccent(coalesce(modalidade, ''))) not like '%adesa%'
      and lower(unaccent(coalesce(modalidade, ''))) not like '%carona%'
),

adesoes_internas as (
    select
        l.portal_slug,
        l.ano,
        l.empresa_id,
        'adesao_ata_interna' as tipo_contratacao,
        l.licitacao_numero as numero,
        l.licitacao_numero,
        c.contrato_numero,
        c.fornecedor_nome,
        coalesce(l.discriminacao, l.licitacao_numero) as objeto,
        'adesao_ata_interna' as modalidade,
        null::text as fundlegal,
        'S' as carona,
        nullif(c.mes, '')::integer as mes,
        null::text as numero_obra,
        null::text as tipo_obra,
        1::integer as quantidade,
        coalesce(l.valor, 0)::numeric(15, 2) as licitacao_valor,
        coalesce(c.valor_contrato, 0)::numeric(15, 2) as valor_contrato,
        coalesce(c.empenhado, 0)::numeric(15, 2) as empenhado_contrato,
        0::numeric(15, 2) as pago_contrato,
        null::date as data_referencia
    from {{ ref('fct_licitacoes') }} l
    left join {{ ref('fct_contratos') }} c
        on c.licitacao_numero = l.licitacao_numero
        and c.empresa_id = l.empresa_id
        and c.portal_slug = l.portal_slug
    where l.carona = 'S'
       or lower(unaccent(coalesce(l.modalidade, ''))) like '%adesa%'
       or lower(unaccent(coalesce(l.modalidade, ''))) like '%carona%'
),

adesoes_externas as (
    select
        dg.portal_slug,
        dg.ano,
        dg.empresa_id,
        'adesao_ata_externa' as tipo_contratacao,
        coalesce(dg.licitacao_numero, dg.despesa_id) as numero,
        coalesce(dg.licitacao_numero, '') as licitacao_numero,
        null::text as contrato_numero,
        dg.fornecedor_nome,
        dg.descricao as objeto,
        'adesao_ata_externa' as modalidade,
        null::text as fundlegal,
        'S' as carona,
        nullif(dg.mes, '')::integer as mes,
        null::text as numero_obra,
        null::text as tipo_obra,
        1::integer as quantidade,
        0::numeric(15, 2) as licitacao_valor,
        coalesce(dg.empenhado, 0)::numeric(15, 2) as valor_contrato,
        coalesce(dg.empenhado, 0)::numeric(15, 2) as empenhado_contrato,
        coalesce(dg.pago, 0)::numeric(15, 2) as pago_contrato,
        dg.data_empenho as data_referencia
    from {{ ref('fct_despesas') }} dg
    where lower(unaccent(coalesce(dg.descricao, ''))) like '%ata de registro de pre%'
       or lower(unaccent(coalesce(dg.descricao, ''))) like '%adesao%ata%'
       or lower(unaccent(coalesce(dg.descricao, ''))) like '%termo de adesao%'
),

licitacoes_gaps as (
    select
        portal_slug,
        ano,
        empresa_id,
        'gap_licitacao' as tipo_contratacao,
        contrato_numero as numero,
        coalesce(trim(licitacao_numero), '') as licitacao_numero,
        contrato_numero,
        fornecedor_nome,
        objeto,
        coalesce(nullif(trim(modalidade), ''), 'sem_licitacao') as modalidade,
        fundlegal,
        'N' as carona,
        nullif(mes, '')::integer as mes,
        numero_obra,
        tipo_obra,
        1::integer as quantidade,
        0::numeric(15, 2) as licitacao_valor,
        coalesce(valor_contrato, 0)::numeric(15, 2) as valor_contrato,
        coalesce(empenhado, 0)::numeric(15, 2) as empenhado_contrato,
        0::numeric(15, 2) as pago_contrato,
        null::date as data_referencia
    from {{ ref('fct_contratos') }}
    where licitacao_numero is null or trim(licitacao_numero) = ''
),

unificado as (
    select * from licitacoes_proprias
    union all
    select * from adesoes_internas
    union all
    select * from adesoes_externas
    union all
    select * from licitacoes_gaps
),

com_limites as (
    select
        u.*,
        coalesce(c.valor_num, 50000.00)::numeric(15, 2) as limite_dispensa,
        (
            lower(unaccent(coalesce(u.modalidade, ''))) like '%inexig%'
            or lower(unaccent(coalesce(u.fundlegal, ''))) like '%inexig%'
            or lower(unaccent(coalesce(u.fornecedor_nome, ''))) like '%consorcio%'
            or lower(unaccent(coalesce(u.objeto, ''))) like '%rateio%'
            or lower(unaccent(coalesce(u.objeto, ''))) like '%contrato de programa%'
            or lower(unaccent(coalesce(u.objeto, ''))) like '%cont. programa%'
        ) as isento_legalmente,
        (
            u.tipo_contratacao = 'gap_licitacao'
            and u.valor_contrato > coalesce(c.valor_num, 50000.00)
            and not (
                lower(unaccent(coalesce(u.modalidade, ''))) like '%inexig%'
                or lower(unaccent(coalesce(u.fundlegal, ''))) like '%inexig%'
                or lower(unaccent(coalesce(u.fornecedor_nome, ''))) like '%consorcio%'
                or lower(unaccent(coalesce(u.objeto, ''))) like '%rateio%'
                or lower(unaccent(coalesce(u.objeto, ''))) like '%contrato de programa%'
                or lower(unaccent(coalesce(u.objeto, ''))) like '%cont. programa%'
            )
        ) as acima_limite
    from unificado u
    left join {{ ref('seed_constantes_fiscais') }} c
        on c.dominio = 'licitacoes'
       and c.ano_inicio <= u.ano
       and c.ano_fim >= u.ano
       and c.chave = case
           when (u.numero_obra is not null and trim(u.numero_obra) != '')
             or (u.tipo_obra is not null and trim(u.tipo_obra) != '')
             or lower(unaccent(coalesce(u.objeto, ''))) like '%obra%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%engenharia%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%reforma%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%construcao%'
           then 'limite_dispensa_obras_engenharia'
           when lower(unaccent(coalesce(u.objeto, ''))) like '%veiculo%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%automovel%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%motocicleta%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%caminhao%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%onibus%'
             or lower(unaccent(coalesce(u.objeto, ''))) like '%frota%'
           then 'limite_dispensa_veiculos'
           else 'limite_dispensa_compras_servicos'
       end
),

com_row_num as (
    select
        *,
        row_number() over (
            partition by portal_slug, ano, empresa_id, tipo_contratacao, numero, coalesce(contrato_numero, ''), coalesce(fornecedor_nome, '')
            order by objeto
        ) as rn
    from com_limites
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'tipo_contratacao', 'numero', "coalesce(contrato_numero, '')", "coalesce(fornecedor_nome, '')", "rn::text"]) }} as licitacao_metricas_id,
    portal_slug,
    ano,
    empresa_id,
    tipo_contratacao,
    numero,
    licitacao_numero,
    contrato_numero,
    fornecedor_nome,
    objeto,
    modalidade,
    fundlegal,
    carona,
    mes,
    numero_obra,
    tipo_obra,
    quantidade,
    licitacao_valor,
    valor_contrato,
    empenhado_contrato,
    pago_contrato,
    data_referencia,
    limite_dispensa,
    isento_legalmente,
    acima_limite
from com_row_num
