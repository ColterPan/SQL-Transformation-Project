-- Partial fuzzy-dedup pass: groups customers who share phone + address + city + zip
-- (a strong signal of the same person re-entered under a nickname variant) and assigns
-- a canonical_customer_id (the lowest id in the group). This will NOT catch every fuzzy
-- duplicate in the manifest -- e.g. duplicates entered with a different phone/address --
-- it is a documented, deliberately partial solution. See data_quality_manifest.md.

with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    customer_id,
    min(customer_id) over (
        partition by phone, address, city, zip
    ) as canonical_customer_id,
    count(*) over (
        partition by phone, address, city, zip
    ) > 1 as is_likely_duplicate
from customers
