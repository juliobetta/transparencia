-- Fato: contratos consolidados de todos os portais

with contratos as (
    select
        portal_slug,
        ano,
        empresa_id,
        contrato_numero,
        fornecedor_nome,
        objeto,
        valor_contrato,
        licitacao_numero,
        modalidade,
        mes,
        tipo_obra,
        numero_obra,
        fundlegal,
        empenhado
    from {{ ref('int_contratos_consolidados') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'contrato_numero']) }} as contrato_id,
    portal_slug,
    ano,
    empresa_id,
    contrato_numero,
    fornecedor_nome,
    objeto,
    valor_contrato,
    licitacao_numero,
    modalidade,
    mes,
    tipo_obra,
    numero_obra,
    fundlegal,
    empenhado
from contratos
