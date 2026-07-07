-- No vehicle should have more than one completed sale in the cleaned mart.
select
    vehicle_id,
    count(*) as completed_sale_count
from {{ ref('fct_sales_transactions') }}
where sale_status = 'completed'
group by vehicle_id
having count(*) > 1
