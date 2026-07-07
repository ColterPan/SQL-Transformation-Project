-- completed_at must never be before started_at wherever both are known.
select
    service_order_id,
    started_at,
    completed_at
from {{ ref('fct_service_orders') }}
where completed_at is not null
  and completed_at < started_at
