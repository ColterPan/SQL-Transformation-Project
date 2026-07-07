-- A vehicle cannot be sold before the dealership acquired it.
select
    sales.transaction_id,
    sales.sale_date,
    vehicles.acquisition_date
from {{ ref('fct_sales_transactions') }} as sales
join {{ ref('dim_vehicles') }} as vehicles using (vehicle_id)
where sales.sale_date < vehicles.acquisition_date
