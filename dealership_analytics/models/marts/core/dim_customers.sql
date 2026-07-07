select
    customers.customer_id,
    customers.first_name,
    customers.last_name,
    customers.email_cleaned as email,
    customers.is_valid_email,
    customers.phone,
    customers.address,
    customers.city,
    customers.state,
    customers.zip,
    customers.date_of_birth,
    customers.is_valid_date_of_birth,
    customers.created_at,
    dedup.canonical_customer_id,
    dedup.is_likely_duplicate
from {{ ref('stg_customers') }} as customers
left join {{ ref('int_customer_dedup') }} as dedup using (customer_id)
