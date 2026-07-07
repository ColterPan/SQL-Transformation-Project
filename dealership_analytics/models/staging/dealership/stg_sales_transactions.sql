with source as (
    select * from {{ source('dealership', 'raw_sales_transactions') }}
)

select
    transaction_id,
    vehicle_id,
    customer_id,
    salesperson_id,
    dealership_id,
    cast(sale_date as date) as sale_date,
    sale_price,
    nullif(trade_in_vehicle_id, '')::bigint as trade_in_vehicle_id,
    case
        when lower(trim(financing_type)) = 'leasee' then 'lease'
        else lower(trim(financing_type))
    end as financing_type,
    sale_status
from source
