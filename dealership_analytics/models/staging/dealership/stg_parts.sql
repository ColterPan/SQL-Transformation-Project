with source as (
    select * from {{ source('dealership', 'raw_parts') }}
)

select
    part_id,
    regexp_replace(
        upper(replace(replace(part_number, ' ', ''), '-', '')),
        '^([A-Z]+)([0-9]+)$', '\1-\2'
    ) as part_number,
    part_name,
    category,
    unit_cost,
    unit_price,
    quantity_on_hand,
    dealership_id
from source
