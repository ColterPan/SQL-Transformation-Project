with source as (
    select * from {{ source('dealership', 'raw_technicians') }}
)

select
    technician_id,
    dealership_id,
    first_name,
    last_name,
    certification_level,
    cast(hire_date as date) as hire_date
from source
