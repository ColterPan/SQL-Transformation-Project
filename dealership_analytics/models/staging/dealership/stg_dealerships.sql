with source as (
    select * from {{ source('dealership', 'raw_dealerships') }}
)

select
    dealership_id,
    name as dealership_name,
    address,
    city,
    {{ clean_state('state') }} as state,
    zip,
    {{ clean_phone('phone') }} as phone,
    region
from source
