-- Payments applied against a sale or service order shouldn't exceed the referenced total
-- by more than a small tolerance (catches overpayment / bad reference bugs). Configured to
-- warn, not fail the build: this project doesn't correct payment amounts, only flags them --
-- a real pipeline would route these to a finance-review queue. See data_quality_manifest.md.
{{ config(severity='warn') }}

with payments as (
    select * from {{ ref('stg_payments') }}
),

sale_totals as (
    select transaction_id as reference_id, sale_price as reference_total
    from {{ ref('fct_sales_transactions') }}
),

service_totals as (
    select service_order_id as reference_id, total_amount as reference_total
    from {{ ref('fct_service_orders') }}
),

payments_with_totals as (
    select
        payments.reference_type,
        payments.reference_id,
        sum(payments.amount) as total_paid,
        coalesce(sale_totals.reference_total, service_totals.reference_total) as reference_total
    from payments
    left join sale_totals
        on payments.reference_type = 'sale' and payments.reference_id = sale_totals.reference_id
    left join service_totals
        on payments.reference_type = 'service' and payments.reference_id = service_totals.reference_id
    group by 1, 2, 4
)

select *
from payments_with_totals
where reference_total is not null
  and total_paid > reference_total + 50
