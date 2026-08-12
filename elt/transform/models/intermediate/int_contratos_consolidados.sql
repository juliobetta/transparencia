-- Intermediário: consolida contratos de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        contrato_numero,
        fornecedor_nome,
        fornecedor_cpf_cnpj,
        objeto,
        objeto_completo,
        valor_contrato,
        valor_aditado,
        licitacao_numero,
        modalidade,
        mes,
        tipo_obra,
        numero_obra,
        fundlegal,
        empenhado,
        data_inicio,
        vencimento_atual,
        saldo_a_empenhar
    from {{ ref('stg_porciuncula_prefeitura__contratos') }}
)

select
    portal_slug,
    ano,
    empresa_id,
    contrato_numero,
    fornecedor_nome,
    fornecedor_cpf_cnpj,
    objeto,
    objeto_completo,
    valor_contrato,
    valor_aditado,
    licitacao_numero,
    modalidade,
    mes,
    tipo_obra,
    numero_obra,
    fundlegal,
    empenhado,
    data_inicio,
    vencimento_atual,
    saldo_a_empenhar
from porciuncula
