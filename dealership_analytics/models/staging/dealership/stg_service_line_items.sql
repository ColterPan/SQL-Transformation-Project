with source as (
    select * from {{ source('dealership', 'raw_service_line_items') }}
)

select
    line_item_id,
    service_order_id,
    nullif(part_id, '')::bigint as part_id,
    lower(trim(line_type)) as line_type,
    description,
    quantity,
    unit_price,
    line_total
from source
