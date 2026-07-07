{% macro clean_state(column_name) %}
    case trim(lower({{ column_name }}))
        when 'california' then 'CA'
        when 'texas' then 'TX'
        when 'new york' then 'NY'
        when 'florida' then 'FL'
        when 'washington' then 'WA'
        when 'illinois' then 'IL'
        when 'colorado' then 'CO'
        when 'arizona' then 'AZ'
        else upper(trim({{ column_name }}))
    end
{% endmacro %}
