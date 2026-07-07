with source as (
    select * from {{ source('dealership', 'raw_service_orders') }}
)

select
    service_order_id,
    nullif(vehicle_id, '')::bigint as vehicle_id,
    customer_id,
    technician_id,
    dealership_id,
    cast(started_at as timestamp) as started_at,
    try_cast(nullif(completed_at, '') as timestamp) as completed_at,
    odometer_reading,
    status,
    total_amount
from source
