-- The mart's recomputed total_amount must equal the sum of its own valid line items.
select
    orders.service_order_id,
    orders.total_amount,
    sum(line_items.line_total) as line_item_sum
from {{ ref('fct_service_orders') }} as orders
join {{ ref('fct_service_line_items') }} as line_items using (service_order_id)
where line_items.is_valid_line
group by orders.service_order_id, orders.total_amount
having abs(orders.total_amount - sum(line_items.line_total)) > 0.01
