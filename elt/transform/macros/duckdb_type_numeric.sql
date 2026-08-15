{% macro duckdb__get_assert_columns_equivalent(sql_columns, yaml_columns=none) %}
    {% if not yaml_columns %}
        {{ return("") }}
    {% endif %}
    {% set actual_type = sql_columns.data_type | default('') | lower %}
    {% set expected_type = yaml_columns.data_type | default('') | lower %}
    {% if ('decimal' in actual_type or 'numeric' in actual_type or 'double' in actual_type or 'float' in actual_type) and ('decimal' in expected_type or 'numeric' in expected_type or 'double' in expected_type or 'float' in expected_type) %}
        {{ return("") }}
    {% else %}
        {{ return(default__get_assert_columns_equivalent(sql_columns, yaml_columns)) }}
    {% endif %}
{% endmacro %}
