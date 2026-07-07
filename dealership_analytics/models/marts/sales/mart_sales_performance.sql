select
    date_trunc('month', sale_date) as sale_month,
    dealership_id,
    salesperson_id,
    count(*) as vehicles_sold,
    sum(sale_price) as total_revenue,
    round(avg(sale_price), 2) as avg_sale_price
from {{ ref('fct_sales_transactions') }}
where sale_status = 'completed'
group by 1, 2, 3
