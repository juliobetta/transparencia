-- Intermediário: consolida contratos de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        contrato_numero,
        fornecedor_nome,
        objeto,
        valor_contrato,
        licitacao_numero,
        mes,
        tipo_obra,
        numero_obra,
        empenhado
    from {{ ref('stg_porciuncula_prefeitura__contratos') }}
)

select
    portal_slug,
    ano,
    empresa_id,
    contrato_numero,
    fornecedor_nome,
    objeto,
    valor_contrato,
    licitacao_numero,
    mes,
    tipo_obra,
    numero_obra,
    empenhado
from porciuncula
