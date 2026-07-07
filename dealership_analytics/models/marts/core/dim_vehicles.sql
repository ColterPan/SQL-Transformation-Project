with vehicles as (
    select * from {{ ref('stg_vehicles') }}
),

sale_status as (
    select * from {{ ref('int_vehicle_sale_status') }}
)

select
    vehicles.vehicle_id,
    vehicles.vin,
    vehicles.make,
    vehicles.model,
    vehicles.model_year,
    vehicles."trim",
    vehicles.color,
    vehicles.mileage,
    vehicles.condition,
    vehicles.acquisition_date,
    vehicles.list_price,
    vehicles.cost,
    -- corrected against actual completed sales, replacing the raw (sometimes stale) status flag
    sale_status.actual_sale_status as status,
    vehicles.status as recorded_status_raw,
    sale_status.status_matches,
    vehicles.title_status,
    vehicles.dealership_id,
    vehicles.cost > 0 and vehicles.list_price > 0 and vehicles.list_price >= vehicles.cost as is_valid_pricing,
    count(*) over (partition by vehicles.vin) > 1 as is_duplicate_vin
from vehicles
join sale_status using (vehicle_id)
