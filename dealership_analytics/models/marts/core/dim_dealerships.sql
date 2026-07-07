select
    dealership_id,
    dealership_name,
    address,
    city,
    state,
    zip,
    phone,
    region
from {{ ref('stg_dealerships') }}
