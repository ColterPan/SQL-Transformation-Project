with source as (
    select * from {{ source('dealership', 'raw_leads') }}
)

select
    lead_id,
    nullif(customer_id, '')::bigint as customer_id,
    case trim(lower(source_channel))
        when 'referal' then 'referral'
        else trim(lower(source_channel))
    end as source_channel,
    campaign_name,
    cast(created_at as timestamp) as created_at,
    converted_flag
from source
