-- Dimensão: calendário diário de 2021 a 2035

with date_spine as (
    select generate_series('2021-01-01'::date, '2035-12-31'::date, '1 day'::interval)::date as data
)

select
    data,
    extract(year from data)::int as ano,
    extract(month from data)::int as mes_num,
    extract(day from data)::int as dia,
    extract(dow from data)::int as dia_semana,
    to_char(data, 'TMMonth') as mes_nome,
    date_trunc('month', data)::date as inicio_mes,
    (date_trunc('month', data) + interval '1 month - 1 day')::date as fim_mes,
    extract(quarter from data)::int as trimestre
from date_spine
