-- A salvage-titled vehicle cannot be listed as a certified pre-owned unit in stock.
-- Configured to warn, not fail the build: this is a listing-desk compliance issue that
-- needs human review, not something the pipeline can safely auto-correct. See manifest.
{{ config(severity='warn') }}

select vehicle_id, title_status, condition, status
from {{ ref('dim_vehicles') }}
where title_status = 'salvage'
  and condition = 'certified'
  and status = 'in_stock'
