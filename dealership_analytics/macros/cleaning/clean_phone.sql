{% macro clean_phone(column_name) %}
    (case
        when length(regexp_replace({{ column_name }}, '[^0-9]', '', 'g')) = 11
            and left(regexp_replace({{ column_name }}, '[^0-9]', '', 'g'), 1) = '1'
            then substr(regexp_replace({{ column_name }}, '[^0-9]', '', 'g'), 2)
        else regexp_replace({{ column_name }}, '[^0-9]', '', 'g')
    end)
{% endmacro %}
