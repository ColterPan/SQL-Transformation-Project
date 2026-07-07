with source as (
    select * from {{ source('dealership', 'raw_payments') }}
)

select
    payment_id,
    reference_type,
    reference_id,
    cast(payment_date as date) as payment_date,
    amount,
    method
from source
