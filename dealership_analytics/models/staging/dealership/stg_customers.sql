with source as (
    select * from {{ source('dealership', 'raw_customers') }}
),

deduped as (
    -- collapses exact-duplicate rows (same person data, different customer_id) to the lowest id
    select
        *,
        row_number() over (
            partition by first_name, last_name, phone, address, city, state, zip, date_of_birth
            order by customer_id
        ) as dupe_rank
    from source
),

cleaned as (
    select
        customer_id,
        first_name,
        last_name,
        trim(lower(nullif(email, ''))) as email_cleaned,
        email as email_raw,
        nullif(email, '') is not null
            and regexp_matches(email, '^[^@\s]+@[^@\s]+\.[^@\s]+$') as is_valid_email,
        {{ clean_phone('phone') }} as phone,
        address,
        city,
        {{ clean_state('state') }} as state,
        zip,
        coalesce(
            try_strptime(date_of_birth, '%m/%d/%Y'),
            try_strptime(date_of_birth, '%Y-%m-%d')
        )::date as date_of_birth,
        cast(created_at as timestamp) as created_at
    from deduped
    where dupe_rank = 1
)

select
    *,
    date_diff('year', date_of_birth, current_date) between 16 and 100 as is_valid_date_of_birth
from cleaned
