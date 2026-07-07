# Demo Walkthrough

All output below is real, captured from an actual run of this project (seed 42) — not
hypothetical. Follow along by running the same commands yourself.

## The problem

A dealership's sales, service, and inventory data comes from three different intake points
(front desk, service bay, and a CRM) that don't agree on formats and occasionally lose track of
each other's records. The result: phone numbers in four formats, the same VIN entered twice,
repair order totals that don't match their own line items, and a spreadsheet of "official"
numbers nobody can reproduce. This project simulates that scenario end to end and fixes it with
a tested dbt pipeline.

## Step 1 — Generate the mess

```powershell
python scripts/generate_raw_data.py --seed 42
```

```
wrote raw_dealerships.csv (6 rows)
wrote raw_salespeople.csv (30 rows)
wrote raw_technicians.csv (25 rows)
wrote raw_customers.csv (5201 rows)
wrote raw_leads.csv (3000 rows)
wrote raw_vehicles.csv (4040 rows)
wrote raw_sales_transactions.csv (3030 rows)
wrote raw_parts.csv (500 rows)
wrote raw_service_orders.csv (6000 rows)
wrote raw_service_line_items.csv (17802 rows)
wrote raw_payments.csv (6397 rows)
done: 46031 rows across 11 tables (seed=42)
```

Every rule that injects a data quality issue is documented in
[`data_quality_manifest.md`](data_quality_manifest.md). A few examples, queried straight from
the raw seed data:

**Phone number chaos** (`raw_customers.phone`):

```
(663) 193-1491
+1 498.776.9453
8083136783
4313518233
710-947-7752
```

**State format chaos** (`raw_customers.state`):

```
tx / fl / illinois  / AZ / arizona  / florida  / colorado  / TX / Florida / Texas / az / ca
```

**The same VIN entered under two different inventory rows** (`raw_vehicles`):

```
vin                  row_count
AGFJZJD89G8VGW1Z3    2
1N096NGFFP0VMX17U    2
GV9E56TYXVHF31G7S    2
```

**Repair order totals that don't match their own line items** (`raw_service_orders` vs.
`raw_service_line_items`):

```
service_order_id   recorded_total   line_item_sum   variance
80222              2066.02          2014.76         51.26
80748              4951.81          4848.76         103.05
81920              3655.36          3773.27         -117.91
```

## Step 2 — Load raw data

```powershell
cd dealership_analytics
$env:DBT_PROFILES_DIR = "."
dbt deps
dbt seed
```

Loads all 11 CSVs into DuckDB (`main_raw` schema) — see the row counts above.

## Step 3 — Transform

```powershell
dbt run
```

Runs staging → intermediate → marts (25 models: 14 views, 11 tables) in dependency order.

## Step 4 — Prove it's fixed

```powershell
dbt test
```

```
Finished running 88 data tests ...
Completed with 20 warnings:
Done. PASS=104 WARN=20 ERROR=0 SKIP=0 TOTAL=124
```

(`dbt build` runs seed + run + test together in one command, if you want the "just run
everything" shortcut.)

**0 errors.** The 20 warnings are each a documented, intentional known limitation (see the
"Known limitations" section of the manifest and README) — things like fuzzy customer duplicates
or payment overages that a real pipeline would route to human review, not silently auto-fix.
Staging-layer tests are deliberately permissive (`warn`) because their job is to *document* raw
problems, not gate the build; marts-layer tests are strict (`error`) and all pass.

The same phone numbers and states from Step 1, now normalized in the marts:

**Cleaned phone** (`dim_customers.phone`, normalized to 10 digits):

```
6631931491
4987769453
8083136783
4313518233
7109477752
```

**Cleaned state** (`dim_customers.state`, always a 2-letter code):

```
AZ / CO / TX / FL / WA / CA / IL / NY
```

**Repair order totals now reconcile with their line items, by construction**
(`fct_service_orders.total_amount` is recomputed from `fct_service_line_items`, not trusted
as-recorded):

```sql
select fso.service_order_id, fso.total_amount, sum(fsli.line_total)
from fct_service_orders fso
join fct_service_line_items fsli using (service_order_id)
where fsli.is_valid_line
group by 1, 2
having abs(fso.total_amount - sum(fsli.line_total)) > 0.01;
-- 0 rows
```

Full queries for all of the above live in
[`analyses/data_quality_before_after.sql`](dealership_analytics/analyses/data_quality_before_after.sql).

## Step 5 — Explore the docs and lineage graph

```powershell
dbt docs generate
dbt docs serve
```

Opens a browser at `localhost:8080`. Worth looking at:

- The lineage graph for `fct_service_orders` — traces back through
  `fct_service_line_items -> stg_service_line_items -> raw_service_line_items`, showing exactly
  where the reconciliation fix happens.
- Column-level descriptions on `dim_vehicles` and `dim_customers`, which document which fields
  were corrected vs. only flagged.

## What this demonstrates for a real-world data quality role

- Reproducing a stakeholder complaint ("nobody can reproduce the numbers") as a concrete,
  testable pipeline rather than a one-off spreadsheet fix.
- Distinguishing between **things a pipeline should silently fix** (format normalization,
  recomputing a total from its own line items) and **things that need a human in the loop**
  (compliance flags, payment overages, fuzzy duplicate merges) — and encoding that distinction
  directly in test severity rather than burying it in a Slack thread.
- Writing tests that encode actual business rules ("a salvage-titled vehicle can't be listed as
  certified pre-owned"), not just `not_null`/`unique` schema checks.

## Known limitations / what I'd do next

- Fuzzy customer dedup is partial (phone+address+city+zip match only) — a production version
  would use a proper record-linkage library (e.g. `splink`).
- No orchestration layer (Airflow/Dagster) — out of scope for a single-warehouse demo.
- DuckDB instead of a cloud warehouse — a deliberate choice to keep this a zero-cost,
  zero-infrastructure portfolio piece; the dbt models themselves are warehouse-agnostic.
