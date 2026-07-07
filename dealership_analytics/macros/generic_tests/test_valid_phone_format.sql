{% test valid_phone_format(model, column_name) %}
-- asserts the column holds exactly 10 digits, i.e. already normalized by clean_phone()
select *
from {{ model }}
where {{ column_name }} is not null
  and not regexp_matches({{ column_name }}, '^[0-9]{10}$')
{% endtest %}
