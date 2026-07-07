with source as (
    select * from {{ source('dealership', 'raw_vehicles') }}
),

deduped as (
    -- collapses exact-duplicate rows (same vin/attributes re-entered under a new vehicle_id)
    select
        *,
        row_number() over (
            partition by vin, make, model, model_year, acquisition_date, dealership_id
            order by vehicle_id
        ) as dupe_rank
    from source
)

select
    vehicle_id,
    vin,
    case
        when lower(make) in ('toyota', 'toyata') then 'Toyota'
        else {{ title_case('make') }}
    end as make,
    model,
    model_year,
    "trim", -- no dirtiness was injected on this column
    color,
    cast(regexp_replace(mileage, '[^0-9]', '', 'g') as integer) as mileage,
    condition,
    cast(acquisition_date as date) as acquisition_date,
    list_price,
    cost,
    status,
    nullif(lower(trim(title_status)), '') as title_status,
    dealership_id
from deduped
where dupe_rank = 1
