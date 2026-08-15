-- Staging: contratos
-- Casts text → numeric e padroniza nomes de colunas.

with source as (
    select * from {{ source('porciuncula_prefeitura', 'contratos') }}
),

renamed as (
    select
        ano::int as ano,
        empresa as empresa_id,
        numero as contrato_numero,
        nullif(trim(fornecedor), '') as fornecedor_nome,
        nullif(trim(objeto), '') as objeto,
        nullif(trim(objeto_completo), '') as objeto_completo,
        nullif(replace(replace(trim(valcon), '.', ''), ',', '.'), '')::numeric(15, 2) as valor_contrato,
        nullif(trim(licitacao_numero), '') as licitacao_numero,
        nullif(trim(modali), '') as modalidade,
        nullif(trim(mes), '') as mes,
        nullif(trim(tipocoobra), '') as tipo_obra,
        nullif(trim(numobra), '') as numero_obra,
        nullif(trim(fundlegal), '') as fundlegal,
        nullif(replace(replace(trim(empenhado), '.', ''), ',', '.'), '')::numeric(15, 2) as empenhado,
        nullif(trim(insmf), '') as fornecedor_cpf_cnpj,
        nullif(replace(replace(trim(aditado), '.', ''), ',', '.'), '')::numeric(15, 2) as valor_aditado,
        case
            when nullif(trim(data_inicio), '') is null then null
            when trim(data_inicio) ~ '^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}.*' then to_date(left(trim(data_inicio), 10), 'DD/MM/YYYY')
            when trim(data_inicio) ~ '^\d{4}-\d{2}-\d{2}.*' then left(trim(data_inicio), 10)::date
            else null
        end as data_inicio,
        case
            when nullif(trim(vencimento_atual), '') is null then null
            when trim(vencimento_atual) ~ '^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}.*' then to_date(left(trim(vencimento_atual), 10), 'DD/MM/YYYY')
            when trim(vencimento_atual) ~ '^\d{4}-\d{2}-\d{2}.*' then left(trim(vencimento_atual), 10)::date
            else null
        end as vencimento_atual,
        nullif(replace(replace(trim(saldoempenhar), '.', ''), ',', '.'), '')::numeric(15, 2) as saldo_a_empenhar
    from source
)

select
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
from renamed
qualify row_number() over (partition by ano, empresa_id, contrato_numero order by valor_contrato desc nulls last, empenhado desc nulls last) = 1
