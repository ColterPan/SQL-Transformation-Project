select
    technician_id,
    dealership_id,
    first_name,
    last_name,
    certification_level,
    hire_date
from {{ ref('stg_technicians') }}
