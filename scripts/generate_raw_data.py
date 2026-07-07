"""
Generates intentionally messy raw CSVs for the dealership dbt project.

Every corruption rule applied below is documented in
`data_quality_manifest.md` at the repo root -- that file and this script
must stay in sync. Run with a fixed --seed for reproducible output.

Usage:
    python scripts/generate_raw_data.py --seed 42 --out dealership_analytics/seeds/raw
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

MAKES_MODELS = {
    "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Tacoma"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Odyssey"],
    "Ford": ["F-150", "Escape", "Explorer", "Mustang", "Edge"],
    "Chevrolet": ["Silverado", "Equinox", "Malibu", "Tahoe", "Traverse"],
    "Nissan": ["Altima", "Rogue", "Sentra", "Pathfinder", "Frontier"],
    "Jeep": ["Grand Cherokee", "Wrangler", "Cherokee", "Compass"],
    "Hyundai": ["Elantra", "Tucson", "Santa Fe", "Sonata"],
    "BMW": ["3 Series", "5 Series", "X3", "X5"],
}
COLORS = ["Black", "White", "Silver", "Gray", "Red", "Blue", "Green"]
CONDITIONS = ["new", "used", "certified"]
TITLE_STATUSES = ["clean", "salvage", "rebuilt"]
FINANCING_TYPES = ["cash", "finance", "lease"]
PART_CATEGORIES = ["brakes", "engine", "electrical", "body", "tires", "fluids"]
LEAD_CHANNELS = ["web", "walk-in", "referral", "phone", "third_party_site"]
STATES = [
    ("CA", "California"), ("TX", "Texas"), ("NY", "New York"),
    ("FL", "Florida"), ("WA", "Washington"), ("IL", "Illinois"),
    ("CO", "Colorado"), ("AZ", "Arizona"),
]

VIN_CHARS = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # excludes I, O, Q per VIN spec


def pct(rng: random.Random, rate: float) -> bool:
    return rng.random() < rate


def random_vin(rng: random.Random) -> str:
    return "".join(rng.choice(VIN_CHARS) for _ in range(17))


def messy_phone(rng: random.Random, fake: Faker) -> str:
    digits = fake.numerify("##########")
    fmt = rng.choice(
        [
            f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}",
            f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}",
            digits,
            f"+1 {digits[0:3]}.{digits[3:6]}.{digits[6:10]}",
        ]
    )
    return fmt


def messy_state(rng: random.Random) -> str:
    abbr, full = rng.choice(STATES)
    variant = rng.choice(["abbr", "abbr_lower", "full", "full_trailing_space"])
    if variant == "abbr":
        return abbr
    if variant == "abbr_lower":
        return abbr.lower()
    if variant == "full":
        return full
    return full.lower() + " "


def messy_dob(rng: random.Random, fake: Faker) -> tuple[str, date]:
    if pct(rng, 0.01):
        # invalid age: either too old (>100) or too young (<16)
        if pct(rng, 0.5):
            dob = date.today() - timedelta(days=365 * rng.randint(101, 110))
        else:
            dob = date.today() - timedelta(days=365 * rng.randint(5, 15))
    else:
        dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
    fmt = rng.choice(["mdy", "iso"])
    text = dob.strftime("%m/%d/%Y") if fmt == "mdy" else dob.strftime("%Y-%m-%d")
    return text, dob


def messy_make_model(rng: random.Random) -> tuple[str, str]:
    make = rng.choice(list(MAKES_MODELS.keys()))
    model = rng.choice(MAKES_MODELS[make])
    if pct(rng, 0.10):
        make = rng.choice(
            [make.upper(), make.lower(), make.replace("o", "a", 1) if "o" in make else make + "a"]
        )
    return make, model


def messy_title_status(rng: random.Random) -> str:
    base = rng.choice(TITLE_STATUSES)
    if not pct(rng, 0.10):
        return base
    return rng.choice([base.upper(), base.capitalize(), base + " ", ""])


def messy_financing(rng: random.Random) -> str:
    base = rng.choice(FINANCING_TYPES)
    variant = rng.choice(["as_is", "cap", "upper", "trail_space", "typo"])
    if variant == "as_is":
        return base
    if variant == "cap":
        return base.capitalize()
    if variant == "upper":
        return base.upper()
    if variant == "trail_space":
        return base + " "
    return "leasee" if base == "lease" else base


def messy_line_type(rng: random.Random, base: str) -> str:
    return rng.choice([base, base.upper(), base.capitalize()])


def messy_part_number(rng: random.Random, n: int) -> str:
    core = f"ABC-{n:04d}"
    variant = rng.choice(["dash", "nodash", "space"])
    if variant == "dash":
        return core
    if variant == "nodash":
        return core.replace("-", "").lower()
    return core.replace("-", " ")


def messy_lead_channel(rng: random.Random) -> str:
    base = rng.choice(LEAD_CHANNELS)
    variant = rng.choice(["as_is", "upper", "trail_space", "typo"])
    if base == "referral" and variant == "typo":
        return "Referal"
    if variant == "upper":
        return base.upper()
    if variant == "trail_space":
        return base + " "
    return base


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log.info("wrote %s (%d rows)", path.name, len(rows))


def duplicate_some_rows(rng: random.Random, rows: list[dict], id_field: str, next_id: list[int], rate: float) -> None:
    """Appends near-duplicate rows (same content, new surrogate key) to simulate double data entry."""
    n = max(1, int(len(rows) * rate))
    for row in rng.sample(rows, min(n, len(rows))):
        clone = dict(row)
        clone[id_field] = next_id[0]
        next_id[0] += 1
        rows.append(clone)


def build(seed: int, out_dir: Path) -> None:
    rng = random.Random(seed)
    fake = Faker()
    Faker.seed(seed)

    # ---------------------------------------------------------- dealerships
    dealerships = []
    for i in range(1, 7):
        abbr, full = STATES[(i - 1) % len(STATES)]
        dealerships.append(
            {
                "dealership_id": 1000 + i,
                "name": f"{fake.city()} {rng.choice(['Auto Group', 'Motors', 'Automotive'])}",
                "address": fake.street_address(),
                "city": fake.city(),
                "state": abbr,
                "zip": fake.postcode(),
                "phone": messy_phone(rng, fake),
                "region": full,
            }
        )
    dealership_ids = [d["dealership_id"] for d in dealerships]

    # --------------------------------------------------------- salespeople
    salespeople = []
    for i in range(1, 31):
        first, last = fake.first_name(), fake.last_name()
        salespeople.append(
            {
                "salesperson_id": 2000 + i,
                "dealership_id": rng.choice(dealership_ids),
                "first_name": first,
                "last_name": last,
                "email": f"{first.lower()}.{last.lower()}@dealership.example.com",
                "phone": messy_phone(rng, fake),
                "hire_date": fake.date_between(start_date="-8y", end_date="-30d").isoformat(),
            }
        )
    salesperson_ids = [s["salesperson_id"] for s in salespeople]

    # -------------------------------------------------------- technicians
    technicians = []
    for i in range(1, 26):
        first, last = fake.first_name(), fake.last_name()
        technicians.append(
            {
                "technician_id": 3000 + i,
                "dealership_id": rng.choice(dealership_ids),
                "first_name": first,
                "last_name": last,
                "certification_level": rng.choice(["apprentice", "certified", "master"]),
                "hire_date": fake.date_between(start_date="-10y", end_date="-30d").isoformat(),
            }
        )
    technician_ids = [t["technician_id"] for t in technicians]

    # ------------------------------------------------------------ customers
    customers = []
    n_customers = 5000
    for i in range(1, n_customers + 1):
        first, last = fake.first_name(), fake.last_name()
        dob_text, _ = messy_dob(rng, fake)
        email = f"{first.lower()}.{last.lower()}@{fake.free_email_domain()}"
        if pct(rng, 0.02):
            email = rng.choice([email.replace("@", "@@", 1), email.replace("@", "", 1)])
        if pct(rng, 0.05):
            email = ""
        customers.append(
            {
                "customer_id": 10_000 + i,
                "first_name": first,
                "last_name": last,
                "email": email,
                "phone": messy_phone(rng, fake),
                "address": fake.street_address(),
                "city": fake.city(),
                "state": messy_state(rng),
                "zip": fake.postcode(),
                "date_of_birth": dob_text,
                "created_at": fake.date_time_between(start_date="-5y", end_date="now").isoformat(sep=" "),
            }
        )

    # fuzzy duplicate people: clone with a first-name nickname variant
    nickname_swaps = {"Robert": "Bob", "William": "Bill", "Richard": "Rick", "James": "Jim", "Elizabeth": "Liz"}
    next_customer_id = [10_000 + n_customers + 1]
    fuzzy_dupe_count = int(n_customers * 0.03)
    for row in rng.sample(customers, fuzzy_dupe_count):
        clone = dict(row)
        clone["customer_id"] = next_customer_id[0]
        next_customer_id[0] += 1
        clone["first_name"] = nickname_swaps.get(row["first_name"], row["first_name"] + "")
        customers.append(clone)

    duplicate_some_rows(rng, customers, "customer_id", next_customer_id, 0.01)
    customer_ids = [c["customer_id"] for c in customers]

    # ---------------------------------------------------------------- leads
    leads = []
    n_leads = 3000
    for i in range(1, n_leads + 1):
        cust_id = "" if pct(rng, 0.05) else rng.choice(customer_ids)
        leads.append(
            {
                "lead_id": 40_000 + i,
                "customer_id": cust_id,
                "source_channel": messy_lead_channel(rng),
                "campaign_name": rng.choice(["spring_sale", "trade_in_bonus", "0_apr_event", "service_reminder"]),
                "created_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat(sep=" "),
                "converted_flag": rng.choice(["true", "false"]),
            }
        )

    # ------------------------------------------------------------- vehicles
    vehicles = []
    n_vehicles = 4000
    for i in range(1, n_vehicles + 1):
        make, model = messy_make_model(rng)
        cost = round(rng.uniform(8000, 45000), 2)
        list_price = round(cost * rng.uniform(1.05, 1.35), 2)
        if pct(rng, 0.01):
            list_price = round(cost * rng.uniform(0.8, 0.98), 2)  # selling at a loss
        if pct(rng, 0.02):
            cost = round(rng.uniform(-500, 0), 2)  # non-positive cost
        mileage = rng.randint(0, 95000)
        mileage_str = f"{mileage:,} mi" if pct(rng, 0.15) else str(mileage)
        condition = rng.choice(CONDITIONS)
        # a certified pre-owned vehicle can never legitimately carry a salvage title --
        # enforced here so assert_title_status_not_contradicting_listing catches real
        # violations only, not incidental noise from independent random assignment.
        title_status = messy_title_status(rng)
        if condition == "certified":
            while "salvage" in title_status.lower():
                title_status = messy_title_status(rng)
        vehicles.append(
            {
                "vehicle_id": 50_000 + i,
                "vin": random_vin(rng),
                "make": make,
                "model": model,
                "model_year": rng.randint(2016, 2026),
                "trim": rng.choice(["Base", "LE", "XLE", "Sport", "Limited"]),
                "color": rng.choice(COLORS),
                "mileage": mileage_str,
                "condition": condition,
                "acquisition_date": fake.date_between(start_date="-3y", end_date="-1d").isoformat(),
                "list_price": list_price,
                "cost": cost,
                "status": "in_stock",  # finalized below once sales are known
                "title_status": title_status,
                "dealership_id": rng.choice(dealership_ids),
            }
        )

    # duplicate VIN: reuse an existing VIN on a different vehicle_id
    vin_dupe_count = int(n_vehicles * 0.01)
    existing_vins = [v["vin"] for v in vehicles]
    for row in rng.sample(vehicles, vin_dupe_count):
        row["vin"] = rng.choice(existing_vins)

    # exact duplicate rows: whole row re-entered under a new vehicle_id
    next_vehicle_id = [50_000 + n_vehicles + 1]
    duplicate_some_rows(rng, vehicles, "vehicle_id", next_vehicle_id, 0.01)

    vehicle_ids = [v["vehicle_id"] for v in vehicles]
    vehicles_by_id = {v["vehicle_id"]: v for v in vehicles}

    # -------------------------------------------------------- sales_transactions
    sales_transactions = []
    n_sales = 3000
    sold_vehicle_ids = rng.sample(vehicle_ids, n_sales)
    for i, veh_id in enumerate(sold_vehicle_ids, start=1):
        veh = vehicles_by_id[veh_id]
        acquisition = date.fromisoformat(veh["acquisition_date"])
        sale_date = fake.date_between(start_date=acquisition, end_date="today")
        sale_price = round(veh["list_price"] * rng.uniform(0.92, 1.02), 2) if veh["list_price"] > 0 else round(rng.uniform(10000, 30000), 2)
        if pct(rng, 0.01):
            sale_price = round(rng.uniform(-500, 0), 2)
        cust_id = rng.choice(customer_ids)
        if pct(rng, 0.01):
            cust_id = 999_999_999  # orphaned customer
        trade_in = ""
        if pct(rng, 0.25):
            trade_in = rng.choice(vehicle_ids)
            if pct(rng, 0.005):
                trade_in = 888_888_888  # orphaned trade-in vehicle
        sales_transactions.append(
            {
                "transaction_id": 60_000 + i,
                "vehicle_id": veh_id,
                "customer_id": cust_id,
                "salesperson_id": rng.choice(salesperson_ids),
                "dealership_id": veh["dealership_id"],
                "sale_date": sale_date.isoformat(),
                "sale_price": sale_price,
                "trade_in_vehicle_id": trade_in,
                "financing_type": messy_financing(rng),
                "sale_status": "completed",
            }
        )

    # orphaned vehicle_id on a sale (references a vehicle that doesn't exist)
    for row in rng.sample(sales_transactions, max(1, int(n_sales * 0.01))):
        row["vehicle_id"] = 777_777_777

    # double-booked sale: duplicate a transaction (same vehicle/customer/date)
    dupe_transactions = rng.sample(sales_transactions, max(1, int(n_sales * 0.01)))
    next_txn_id = [60_000 + n_sales + 1]
    for row in dupe_transactions:
        clone = dict(row)
        clone["transaction_id"] = next_txn_id[0]
        next_txn_id[0] += 1
        sales_transactions.append(clone)

    # finalize vehicle status now that sales are known
    truly_sold_ids = {t["vehicle_id"] for t in sales_transactions if t["vehicle_id"] in vehicles_by_id}
    for veh_id in truly_sold_ids:
        vehicles_by_id[veh_id]["status"] = "sold"
    # orphaned sold status: mark a few extra vehicles "sold" with no matching transaction
    remaining = [v for v in vehicles if v["status"] != "sold"]
    for row in rng.sample(remaining, min(int(n_vehicles * 0.01), len(remaining))):
        row["status"] = "sold"
    # leave the rest split between in_stock / pending
    for row in vehicles:
        if row["status"] != "sold":
            row["status"] = rng.choice(["in_stock", "in_stock", "pending"])

    # deliberate business-rule violation: a salvage-titled, in-stock vehicle mislabeled
    # as certified pre-owned (~0.5%) -- a real listing-desk data entry error
    certified_in_stock = [v for v in vehicles if v["condition"] == "certified" and v["status"] == "in_stock"]
    for row in rng.sample(certified_in_stock, min(int(n_vehicles * 0.005), len(certified_in_stock))):
        row["title_status"] = "salvage"

    # --------------------------------------------------------------- parts
    parts = []
    n_parts = 500
    for i in range(1, n_parts + 1):
        unit_cost = round(rng.uniform(5, 800), 2)
        unit_price = round(unit_cost * rng.uniform(1.2, 2.0), 2)
        if pct(rng, 0.02):
            unit_price = round(unit_cost * rng.uniform(0.5, 0.95), 2)  # selling at a loss
        qty = rng.randint(0, 200)
        if pct(rng, 0.02):
            qty = -rng.randint(1, 10)
        parts.append(
            {
                "part_id": 70_000 + i,
                "part_number": messy_part_number(rng, i),
                "part_name": rng.choice(
                    ["Brake Pad Set", "Oil Filter", "Alternator", "Headlight Assembly", "Tire", "Battery", "Radiator", "Spark Plug"]
                ),
                "category": rng.choice(PART_CATEGORIES),
                "unit_cost": unit_cost,
                "unit_price": unit_price,
                "quantity_on_hand": qty,
                "dealership_id": rng.choice(dealership_ids),
            }
        )
    part_ids = [p["part_id"] for p in parts]

    # --------------------------------------------------------- service_orders
    service_orders = []
    n_orders = 6000
    last_odometer_by_vehicle: dict[int, int] = {}
    for i in range(1, n_orders + 1):
        veh_id = rng.choice(vehicle_ids) if pct(rng, 0.85) else ""  # walk-ins with no inventory record
        started = fake.date_time_between(start_date="-2y", end_date="now")
        duration_hours = rng.uniform(0.5, 72)
        completed = started + timedelta(hours=duration_hours)
        status = rng.choice(["completed", "completed", "completed", "in_progress", "open", "cancelled"])
        if pct(rng, 0.02):
            completed = started - timedelta(hours=rng.uniform(1, 10))  # impossible interval
        completed_val = completed.isoformat(sep=" ")
        if status == "completed" and pct(rng, 0.01):
            completed_val = ""  # completed but no timestamp
        odometer = rng.randint(500, 120000)
        if veh_id and veh_id in last_odometer_by_vehicle and pct(rng, 0.01):
            odometer = max(0, last_odometer_by_vehicle[veh_id] - rng.randint(500, 5000))  # rollback
        if veh_id:
            last_odometer_by_vehicle[veh_id] = odometer
        tech_id = rng.choice(technician_ids)
        if pct(rng, 0.01):
            tech_id = 666_666_666  # orphaned technician
        service_orders.append(
            {
                "service_order_id": 80_000 + i,
                "vehicle_id": veh_id,
                "customer_id": rng.choice(customer_ids),
                "technician_id": tech_id,
                "dealership_id": rng.choice(dealership_ids),
                "started_at": started.isoformat(sep=" "),
                "completed_at": completed_val,
                "odometer_reading": odometer,
                "status": status,
                "total_amount": 0.0,  # filled in after line items are generated
            }
        )
    service_order_ids = [o["service_order_id"] for o in service_orders]
    orders_by_id = {o["service_order_id"]: o for o in service_orders}

    # ----------------------------------------------------- service_line_items
    service_line_items = []
    line_item_counter = 1
    order_true_totals: dict[int, float] = {}
    for order_id in service_order_ids:
        n_lines = rng.randint(1, 5)
        running_total = 0.0
        for _ in range(n_lines):
            is_part_line = pct(rng, 0.6)
            if is_part_line:
                part_id = rng.choice(part_ids)
                if pct(rng, 0.01):
                    part_id = 555_555_555  # orphaned part
                part = next((p for p in parts if p["part_id"] == part_id), None)
                unit_price = part["unit_price"] if part else round(rng.uniform(10, 500), 2)
                description = part["part_name"] if part else "Unknown Part"
                base_line_type = "part"
            else:
                part_id = ""
                unit_price = round(rng.uniform(50, 300), 2)
                description = rng.choice(["Diagnostic", "Labor - Brake Job", "Labor - Oil Change", "Labor - Inspection"])
                base_line_type = "labor"

            qty = rng.randint(1, 4)
            if pct(rng, 0.01):
                qty = -qty
            if pct(rng, 0.01):
                unit_price = -unit_price

            line_total = round(qty * unit_price, 2)
            if pct(rng, 0.02):
                line_total = round(line_total + rng.uniform(-20, 20), 2)  # arithmetic drift

            service_line_items.append(
                {
                    "line_item_id": 90_000 + line_item_counter,
                    "service_order_id": order_id,
                    "part_id": part_id,
                    "line_type": messy_line_type(rng, base_line_type),
                    "description": description,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )
            line_item_counter += 1
            running_total += line_total
        order_true_totals[order_id] = round(running_total, 2)

    # fill in service_orders.total_amount, with ~2% deliberately broken
    for order_id, order in orders_by_id.items():
        true_total = order_true_totals.get(order_id, 0.0)
        if pct(rng, 0.02):
            order["total_amount"] = round(true_total + rng.uniform(20, 150) * rng.choice([-1, 1]), 2)
        else:
            order["total_amount"] = true_total

    # ------------------------------------------------------------- payments
    payments = []
    n_payment_id = 1
    for order_id, order in orders_by_id.items():
        if order["status"] not in ("completed",) or not pct(rng, 0.9):
            continue
        target = order["total_amount"]
        n_installments = rng.choice([1, 1, 1, 2])
        remaining = target
        for k in range(n_installments):
            amount = round(target / n_installments, 2) if n_installments > 1 else remaining
            if pct(rng, 0.03):
                amount = round(amount + rng.uniform(-30, 30), 2)  # reconciliation break
            payments.append(
                {
                    "payment_id": 100_000 + n_payment_id,
                    "reference_type": "service",
                    "reference_id": order_id,
                    "payment_date": order["started_at"][:10],
                    "amount": amount,
                    "method": rng.choice(["card", "cash", "check", "financing"]),
                }
            )
            n_payment_id += 1
    for txn in sales_transactions:
        if not pct(rng, 0.95):
            continue
        target = txn["sale_price"]
        amount = target
        if pct(rng, 0.02):
            amount = round(target + rng.uniform(-100, 100), 2)
        ref_id = txn["transaction_id"]
        if pct(rng, 0.01):
            ref_id = 444_444_444  # orphaned reference
        payments.append(
            {
                "payment_id": 100_000 + n_payment_id,
                "reference_type": "sale",
                "reference_id": ref_id,
                "payment_date": txn["sale_date"],
                "amount": amount,
                "method": rng.choice(["card", "cash", "check", "financing"]),
            }
        )
        n_payment_id += 1

    # ----------------------------------------------------------------- write
    write_csv(out_dir / "raw_dealerships.csv", dealerships, list(dealerships[0].keys()))
    write_csv(out_dir / "raw_salespeople.csv", salespeople, list(salespeople[0].keys()))
    write_csv(out_dir / "raw_technicians.csv", technicians, list(technicians[0].keys()))
    write_csv(out_dir / "raw_customers.csv", customers, list(customers[0].keys()))
    write_csv(out_dir / "raw_leads.csv", leads, list(leads[0].keys()))
    write_csv(out_dir / "raw_vehicles.csv", vehicles, list(vehicles[0].keys()))
    write_csv(out_dir / "raw_sales_transactions.csv", sales_transactions, list(sales_transactions[0].keys()))
    write_csv(out_dir / "raw_parts.csv", parts, list(parts[0].keys()))
    write_csv(out_dir / "raw_service_orders.csv", service_orders, list(service_orders[0].keys()))
    write_csv(out_dir / "raw_service_line_items.csv", service_line_items, list(service_line_items[0].keys()))
    write_csv(out_dir / "raw_payments.csv", payments, list(payments[0].keys()))

    total_rows = sum(
        len(t)
        for t in [
            dealerships, salespeople, technicians, customers, leads, vehicles,
            sales_transactions, parts, service_orders, service_line_items, payments,
        ]
    )
    log.info("done: %d rows across 11 tables (seed=%d)", total_rows, seed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("dealership_analytics/seeds/raw"))
    args = parser.parse_args()
    build(args.seed, args.out)


if __name__ == "__main__":
    main()
