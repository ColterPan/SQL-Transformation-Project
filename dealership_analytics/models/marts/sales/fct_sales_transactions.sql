with transactions as (
    select * from {{ ref('stg_sales_transactions') }}
    where sale_price > 0  -- excludes ~1% data-entry errors (zero/negative sale price); see manifest
),

deduped as (
    -- collapses double-booked sales (same vehicle+customer+date entered twice under different ids)
    select
        *,
        row_number() over (
            partition by vehicle_id, customer_id, sale_date
            order by transaction_id
        ) as dupe_rank
    from transactions
),

valid_references as (
    -- drops sales referencing a customer or vehicle that doesn't exist in the cleaned dimensions
    select deduped.*
    from deduped
    join {{ ref('dim_customers') }} as customers using (customer_id)
    join {{ ref('dim_vehicles') }} as vehicles using (vehicle_id)
    where deduped.dupe_rank = 1
)

select
    valid_references.transaction_id,
    valid_references.vehicle_id,
    valid_references.customer_id,
    valid_references.salesperson_id,
    valid_references.dealership_id,
    valid_references.sale_date,
    valid_references.sale_price,
    -- nulls out a trade-in reference to a vehicle_id that doesn't exist (~0.5% of rows)
    case
        when valid_references.trade_in_vehicle_id is not null and trade_ins.vehicle_id is null
            then null
        else valid_references.trade_in_vehicle_id
    end as trade_in_vehicle_id,
    valid_references.financing_type,
    valid_references.sale_status
from valid_references
left join {{ ref('dim_vehicles') }} as trade_ins
    on valid_references.trade_in_vehicle_id = trade_ins.vehicle_id
