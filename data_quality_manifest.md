# Data Quality Manifest

This is the single source of truth for every data quality problem intentionally
injected into the raw seed data by [`scripts/generate_raw_data.py`](scripts/generate_raw_data.py).

Every row here maps to either:
- a **staging model** column that cleans/normalizes it (`dealership_analytics/models/staging/`), or
- a **test** that proves the raw layer is dirty and the mart layer is clean
  (`dealership_analytics/tests/`, or a generic test in `_*.yml` files).

If you regenerate the data with a different `--seed`, the *rules* below still hold —
only the exact rows affected change.

## customers
| Issue | Rule | Approx. rate |
|---|---|---|
| Fuzzy duplicate person | Same human, different `customer_id`, minor name variant (e.g. "Bob"/"Robert") | ~3% |
| Phone format chaos | 4 formats: `(555) 123-4567`, `555-123-4567`, `5551234567`, `+1 555.123.4567` | 100% (all rows, random format) |
| State format chaos | `CA`, `ca`, `California`, `california ` (trailing space) | 100% |
| Missing email | `email` is null | ~5% |
| Malformed email | `bob.smith@@gmail`, `bob.smithgmail.com` | ~2% |
| Date-of-birth format chaos | Mixed `MM/DD/YYYY` and `YYYY-MM-DD` text | 100% |
| Invalid age | DOB implies age > 100 or < 16 | ~1% |
| Exact duplicate row | Whole row inserted twice | ~1% |

## vehicles
| Issue | Rule | Approx. rate |
|---|---|---|
| Duplicate VIN | Same VIN, two distinct `vehicle_id` rows | ~1% |
| Make/model typos & casing | `Toyota`/`toyota`/`TOYOTA`/`Toyata` | ~10% of rows |
| Non-positive price | `cost` or `list_price` <= 0 | ~2% |
| Selling at a loss | `list_price` < `cost` | ~1% |
| Title status chaos | `clean`, `Clean`, `SALVAGE`, `rebuilt `, null | ~10% |
| Orphaned sold status | `status = 'sold'` but no matching `sales_transactions` row | ~1% of sold vehicles |
| Salvage listed as certified | `title_status = 'salvage'` on an `in_stock` vehicle with `condition = 'certified'` | ~0.5% of certified in-stock vehicles |
| Mileage as dirty text | `"45,231 mi"` instead of a clean number | ~15% |
| Exact duplicate row | Whole row inserted twice | ~1% |

## sales_transactions
| Issue | Rule | Approx. rate |
|---|---|---|
| Orphaned customer | `customer_id` not in `customers` | ~1% |
| Orphaned vehicle | `vehicle_id` not in `vehicles` | ~1% |
| Non-positive sale price | `sale_price` <= 0 | ~1% |
| Financing type chaos | `cash`, `Cash`, `FINANCE`, `financing`, `Lease `, `leasee` (typo) | 100% |
| Double-booked sale | Same `vehicle_id` + `sale_date` + `customer_id` inserted twice | ~1% |
| Orphaned trade-in | `trade_in_vehicle_id` not in `vehicles` | ~0.5% |

## service_orders
| Issue | Rule | Approx. rate |
|---|---|---|
| Impossible interval | `completed_at` < `started_at` | ~2% |
| Orphaned technician | `technician_id` not in `technicians` | ~1% |
| Odometer rollback | Lower reading than a previous order for same vehicle | ~1% |
| Completed but no timestamp | `status = 'completed'` and `completed_at` is null | ~1% |
| Revenue reconciliation break | `total_amount` != `SUM(service_line_items.line_total)` | ~2% |

## service_line_items
| Issue | Rule | Approx. rate |
|---|---|---|
| Negative quantity/price | `quantity` or `unit_price` < 0 | ~1% |
| Arithmetic drift | `line_total` != `quantity * unit_price` | ~2% |
| Orphaned part | `part_id` not in `parts` (part-type lines only) | ~1% |
| Line-type casing chaos | `Part`, `PART`, `labor`, `Labor` | 100% |

## parts
| Issue | Rule | Approx. rate |
|---|---|---|
| Negative quantity on hand | `quantity_on_hand` < 0 | ~2% |
| Selling at a loss | `unit_cost` > `unit_price` | ~2% |
| Part number format chaos | `ABC-1234`, `abc1234`, `ABC 1234` | 100% |

## payments
| Issue | Rule | Approx. rate |
|---|---|---|
| Reconciliation break | `SUM(amount)` for a `reference_id` doesn't match the referenced total | ~3% |
| Orphaned reference | `reference_id` doesn't match any real transaction/service order | ~1% |

## leads
| Issue | Rule | Approx. rate |
|---|---|---|
| Source channel chaos | `Web`, `WEB`, `web `, `Referal` (typo) | 100% |
| Missing customer | `customer_id` null (anonymous lead capture — allowed, not a bug) | ~5% |

## dealerships, salespeople, technicians
Kept clean (dimension "control group") — no injected dirtiness. This is deliberate:
it demonstrates the generator can produce clean *and* dirty tables side by side, and
keeps a few generic tests trivially green so the test suite isn't 100% red at the
staging layer.

## Known limitations (by design, not oversight)
These are surfaced with `severity: warn` rather than silently fixed or hard-failed, because a
real pipeline would route them to a human review queue, not auto-correct them:
- **Fuzzy customer duplicates** are not resolved by `unique`/`relationships` tests (IDs
  genuinely differ) — see `int_customer_dedup.sql` for a documented, partial fuzzy-match
  approach based on matching phone/address/city/zip.
- **Duplicate VINs** across distinct `vehicle_id` rows are flagged (`is_duplicate_vin`) but
  not merged — deciding which entry is authoritative needs human judgment.
- **Non-positive / loss-making pricing** on vehicles and parts is flagged (`is_valid_pricing`)
  but not corrected — could be a legitimate clearance sale, not necessarily bad data.
- **Salvage-titled vehicles mislabeled as certified pre-owned** is a compliance issue
  (`assert_title_status_not_contradicting_listing`) flagged for the listing desk to fix, not
  auto-relabeled by the pipeline.
- **Payment amounts that overshoot the referenced sale/service total**
  (`assert_payments_reconcile_to_reference_total`) are flagged for finance review, not
  adjusted by the pipeline.
- **Raw arithmetic drift** between `quantity * unit_price` and the recorded `line_total`
  is surfaced at the staging layer for audit (`assert_line_total_matches_quantity_times_price`)
  even though the mart (`fct_service_line_items`) already recomputes the corrected value.
