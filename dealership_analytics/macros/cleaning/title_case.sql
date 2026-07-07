{% macro title_case(column_name) %}
    (upper(substr(trim({{ column_name }}), 1, 1)) || lower(substr(trim({{ column_name }}), 2)))
{% endmacro %}
