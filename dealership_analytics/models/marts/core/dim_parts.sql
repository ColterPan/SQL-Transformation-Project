select
    part_id,
    part_number,
    part_name,
    category,
    unit_cost,
    unit_price,
    quantity_on_hand,
    dealership_id,
    unit_cost > 0 and unit_price > 0 and unit_price >= unit_cost as is_valid_pricing,
    quantity_on_hand >= 0 as is_valid_quantity
from {{ ref('stg_parts') }}
