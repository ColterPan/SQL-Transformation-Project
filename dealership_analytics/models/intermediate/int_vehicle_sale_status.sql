with vehicles as (
    select vehicle_id, status as recorded_status
    from {{ ref('stg_vehicles') }}
),

completed_sales as (
    select distinct vehicle_id
    from {{ ref('stg_sales_transactions') }}
    where sale_status = 'completed'
),

flagged as (
    select
        vehicles.vehicle_id,
        vehicles.recorded_status,
        completed_sales.vehicle_id is not null as has_completed_sale
    from vehicles
    left join completed_sales using (vehicle_id)
)

select
    vehicle_id,
    recorded_status,
    case
        -- a real completed sale always wins, regardless of the recorded inventory status
        when has_completed_sale then 'sold'
        -- orphaned "sold" flag with no matching sale: revert to in_stock (data sync gap)
        when recorded_status = 'sold' and not has_completed_sale then 'in_stock'
        else recorded_status
    end as actual_sale_status,
    (recorded_status = 'sold') = has_completed_sale as status_matches
from flagged
