with line_items as (
    select
        service_order_id,
        sum(line_total) as calculated_total
    from {{ ref('stg_service_line_items') }}
    group by 1
),

orders as (
    select
        service_order_id,
        total_amount as recorded_total
    from {{ ref('stg_service_orders') }}
)

select
    orders.service_order_id,
    orders.recorded_total,
    coalesce(line_items.calculated_total, 0) as calculated_total,
    round(orders.recorded_total - coalesce(line_items.calculated_total, 0), 2) as total_variance,
    abs(orders.recorded_total - coalesce(line_items.calculated_total, 0)) <= 0.01 as totals_reconcile
from orders
left join line_items using (service_order_id)
