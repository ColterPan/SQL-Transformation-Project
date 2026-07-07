-- Ad hoc queries used to fill in the before/after snippets in DEMO.md.
-- Run individual sections with: dbt compile --select data_quality_before_after
-- then paste the compiled SQL into a duckdb session, or run via the Python API.

-- ============================================================ BEFORE: raw layer

-- customers: 4 phone formats side by side
select phone from {{ source('dealership', 'raw_customers') }} limit 8;

-- customers: state format chaos
select distinct state from {{ source('dealership', 'raw_customers') }} limit 12;

-- vehicles: the same VIN entered under two different vehicle_id rows
select vin, count(*) as row_count
from {{ source('dealership', 'raw_vehicles') }}
group by vin
having count(*) > 1
limit 5;

-- service_orders: recorded total vs. what the line items actually sum to
select
    so.service_order_id,
    so.total_amount as recorded_total,
    sum(sli.line_total) as line_item_sum,
    round(so.total_amount - sum(sli.line_total), 2) as variance
from {{ source('dealership', 'raw_service_orders') }} as so
join {{ source('dealership', 'raw_service_line_items') }} as sli using (service_order_id)
group by 1, 2
having abs(so.total_amount - sum(sli.line_total)) > 0.01
limit 5;

-- ============================================================ AFTER: cleaned marts

-- customers: every phone number now normalized to 10 digits
select phone from {{ ref('dim_customers') }} limit 8;

-- customers: state is always a clean 2-letter code
select distinct state from {{ ref('dim_customers') }} limit 12;

-- service_orders: total_amount now equals the sum of its own line items, by construction
select
    fso.service_order_id,
    fso.total_amount,
    sum(fsli.line_total) as line_item_sum
from {{ ref('fct_service_orders') }} as fso
join {{ ref('fct_service_line_items') }} as fsli using (service_order_id)
where fsli.is_valid_line
group by 1, 2
having abs(fso.total_amount - sum(fsli.line_total)) > 0.01
limit 5; -- expected: 0 rows
