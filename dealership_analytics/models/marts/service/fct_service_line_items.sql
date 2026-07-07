with line_items as (
    -- excludes lines whose order was dropped from fct_service_orders (e.g. orphaned technician_id)
    select stg.*
    from {{ ref('stg_service_line_items') }} as stg
    join {{ ref('stg_service_orders') }} as orders using (service_order_id)
    join {{ ref('dim_technicians') }} as technicians on orders.technician_id = technicians.technician_id
)

select
    line_items.line_item_id,
    line_items.service_order_id,
    -- nulls out a part_id reference that doesn't exist in the cleaned parts dimension (~1% of part lines)
    case
        when line_items.part_id is not null and parts.part_id is null then null
        else line_items.part_id
    end as part_id,
    line_items.line_type,
    line_items.description,
    line_items.quantity,
    line_items.unit_price,
    -- recomputed from quantity * unit_price, fixing the arithmetic drift present in the raw data
    round(line_items.quantity * line_items.unit_price, 2) as line_total,
    line_items.quantity > 0 and line_items.unit_price > 0 as is_valid_line
from line_items
left join {{ ref('dim_parts') }} as parts using (part_id)
