select
    salesperson_id,
    dealership_id,
    first_name,
    last_name,
    email,
    phone,
    hire_date
from {{ ref('stg_salespeople') }}
