-- Dimensão: calendário diário de 2021 a 2035
-- Gerado via generate_series para evitar CSV grande

WITH date_spine AS (
    SELECT generate_series('2021-01-01'::DATE, '2035-12-31'::DATE, '1 day'::INTERVAL)::DATE AS data
)

SELECT
    data,
    EXTRACT(YEAR FROM data)::INT AS ano,
    EXTRACT(MONTH FROM data)::INT AS mes_num,
    EXTRACT(DAY FROM data)::INT AS dia,
    EXTRACT(DOW FROM data)::INT AS dia_semana,
    TO_CHAR(data, 'TMMonth') AS mes_nome,
    DATE_TRUNC('month', data)::DATE AS inicio_mes,
    (DATE_TRUNC('month', data) + INTERVAL '1 month - 1 day')::DATE AS fim_mes,
    EXTRACT(QUARTER FROM data)::INT AS trimestre
FROM date_spine
