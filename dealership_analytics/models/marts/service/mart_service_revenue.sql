select
    date_trunc('month', started_at) as service_month,
    dealership_id,
    count(*) as service_orders_count,
    sum(total_amount) as total_service_revenue,
    round(avg(total_amount), 2) as avg_order_value
from {{ ref('fct_service_orders') }}
where status = 'completed'
group by 1, 2
