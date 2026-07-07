with orders as (
    select * from {{ ref('stg_service_orders') }}
),

valid_technician_orders as (
    -- drops orders referencing a technician that doesn't exist (~1% of rows)
    select orders.*
    from orders
    join {{ ref('dim_technicians') }} as technicians using (technician_id)
),

corrected_totals as (
    -- recomputed from valid line items only, fixing the recorded/line-item reconciliation break
    select
        service_order_id,
        sum(line_total) as calculated_total
    from {{ ref('fct_service_line_items') }}
    where is_valid_line
    group by 1
)

select
    valid_technician_orders.service_order_id,
    valid_technician_orders.vehicle_id,
    valid_technician_orders.customer_id,
    valid_technician_orders.technician_id,
    valid_technician_orders.dealership_id,
    valid_technician_orders.started_at,
    -- nulls out a completed_at that is impossibly before started_at (~2% of rows)
    case
        when valid_technician_orders.completed_at < valid_technician_orders.started_at then null
        else valid_technician_orders.completed_at
    end as completed_at,
    valid_technician_orders.completed_at < valid_technician_orders.started_at as has_timestamp_anomaly,
    valid_technician_orders.odometer_reading,
    valid_technician_orders.status,
    coalesce(corrected_totals.calculated_total, 0) as total_amount,
    valid_technician_orders.total_amount as recorded_total_amount_raw
from valid_technician_orders
left join corrected_totals using (service_order_id)
