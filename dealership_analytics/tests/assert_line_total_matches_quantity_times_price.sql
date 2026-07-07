-- Surfaces the raw arithmetic drift between quantity * unit_price and the recorded line_total
-- at the staging layer (fixed downstream in fct_service_line_items -- see that model's docstring).
{{ config(severity='warn') }}

select
    line_item_id,
    quantity,
    unit_price,
    line_total,
    round(quantity * unit_price, 2) as expected_line_total
from {{ ref('stg_service_line_items') }}
where abs(line_total - round(quantity * unit_price, 2)) > 0.01
