with source as (
    select * from {{ source('dealership', 'raw_salespeople') }}
)

select
    salesperson_id,
    dealership_id,
    first_name,
    last_name,
    email,
    {{ clean_phone('phone') }} as phone,
    cast(hire_date as date) as hire_date
from source
