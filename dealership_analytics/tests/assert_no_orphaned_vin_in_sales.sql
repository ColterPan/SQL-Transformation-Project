-- Every vehicle_id in the cleaned sales fact must resolve to a real inventory record --
-- proving the raw-layer orphaned vehicle_id references (see manifest) were excluded.
select sales.transaction_id, sales.vehicle_id
from {{ ref('fct_sales_transactions') }} as sales
left join {{ ref('dim_vehicles') }} as vehicles using (vehicle_id)
where vehicles.vehicle_id is null
