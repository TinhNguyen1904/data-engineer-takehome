{% macro as_of_join(left_table, right_table, left_ts_col, right_effective_col, right_value_cols, alias_right='r') -%}

LEFT JOIN LATERAL (
  SELECT {{ right_value_cols | join(', ') }}
  FROM {{ right_table }}
  WHERE {{ right_effective_col }} <= {{ left_ts_col }}
  ORDER BY {{ right_effective_col }} DESC
  LIMIT 1
) {{ alias_right }}
{% endmacro %}
