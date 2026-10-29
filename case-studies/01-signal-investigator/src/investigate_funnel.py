
"""Investigate changes in ecommerce funnel performance."""

import os
import csv
from pathlib import Path
from src.validate_funnel import validate_dataset


# STEP 1: Locate our project files
ROOT = Path(__file__).resolve().parents[1]

DATA = Path(
    os.environ.get(
        "SIGNAL_FUNNEL_DATA",
        str(ROOT / "data" / "daily_paid_search_funnel.csv")
    )
)

OUTPUT = Path(
    os.environ.get(
        "SIGNAL_FUNNEL_OUTPUT",
        str(ROOT / "outputs" / "funnel_investigation.md")
    )
)


METRICS = [
    "sessions",
    "view_item_sessions",
    "add_to_cart_sessions",
    "begin_checkout_sessions",
    "payment_attempt_sessions",
    "payment_failed_sessions",
    "orders",
]

# STEP 2: Read the CSV and convert values into numbers

# STEP 2: Read and validate the dataset
with DATA.open(newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

# Validate data before calculating metrics
errors = validate_dataset(rows)

if errors:
    print("DATA QUALITY CHECK FAILED")

    for error in errors:
        print(f"- {error}")

    raise SystemExit(
        "Investigation stopped because the data is invalid."
    )

print("Data quality validation passed!")

# Convert validated values into integers
for row in rows:
    for metric in METRICS:
        row[metric] = int(row[metric])


# STEP 3: Separate historical data from the incident
incident_date = "2026-10-13"

historical = [
    row for row in rows
    if row["date"] < incident_date
    and row["channel"] == "paid_search"
]

incident = next(
    row for row in rows
    if row["date"] == incident_date
    and row["channel"] == "paid_search"
)

if not historical:
    raise ValueError("No historical comparison data found.")

# Sum the historical metrics to create weighted baselines
baseline = {
    metric: sum(row[metric] for row in historical)
    for metric in METRICS
}

# STEP 4: Define our conversion-rate calculator
def rate(numerator, denominator):
    if denominator == 0:
        raise ValueError("Cannot calculate rate with zero denominator.")
    return numerator / denominator * 100

# STEP 5: Define the funnel stages
stages = [
    ("Product view / session",
     "view_item_sessions", "sessions"),
    ("Add to cart / product view",
     "add_to_cart_sessions", "view_item_sessions"),
    ("Checkout / cart",
     "begin_checkout_sessions", "add_to_cart_sessions"),
    ("Payment attempt / checkout",
     "payment_attempt_sessions", "begin_checkout_sessions"),
    ("Orders / payment-attempt sessions",
     "orders", "payment_attempt_sessions"),
]

results = []

for name, numerator, denominator in stages:
    before = rate(baseline[numerator], baseline[denominator])
    after = rate(incident[numerator], incident[denominator])
    change = after - before

    results.append((name, before, after, change))

# STEP 6: Identify the largest deterioration
worst = min(results, key=lambda result: result[3])

# Cross-check failed-payment sessions
old_failure = rate(
    baseline["payment_failed_sessions"],
    baseline["payment_attempt_sessions"]
)

new_failure = rate(
    incident["payment_failed_sessions"],
    incident["payment_attempt_sessions"]
)

# STEP 7: Generate a Markdown report
report = [
    "# Funnel Investigation — 2026-10-13",
    "",
    "## Funnel performance",
    "",
    "| Stage | Baseline | Incident | Change (pp) |",
    "|---|---:|---:|---:|",
]

for name, before, after, change in results:
    report.append(
        f"| {name} | {before:.2f}% | {after:.2f}% "
        f"| {change:+.2f} |"
    )

report.extend([
    "",
    "## Biggest deterioration",
    f"**{worst[0]}**",
    f"- Historical: {worst[1]:.2f}%",
    f"- Incident: {worst[2]:.2f}%",
    f"- Change: {worst[3]:+.2f} percentage points",
    "",
    "## Payment failure cross-check",
    f"- Historical affected-session share: {old_failure:.2f}%",
    f"- Incident affected-session share: {new_failure:.2f}%",
    "",
    "## Investigation conclusion",
    "Payment-stage performance deteriorated sharply.",
    "Elevated payment failures support the payment-issue hypothesis.",
    "Root cause remains unverified. Payment logs, error codes "
    "and backend order data are needed.",
    "",
    "## Limitations",
    "Synthetic dataset. Stage metrics represent sessions, "
    "except orders. The demo assumes at most one order per "
    "session. Real funnel reporting should use consistent "
    "session-based or user-based metrics.",
])

OUTPUT.write_text("\n".join(report) + "\n", encoding="utf-8")

# STEP 8: Show results in the terminal
print("Funnel investigation completed!")
print(f"Biggest deterioration: {worst[0]}")
print(f"Historical rate: {worst[1]:.2f}%")
print(f"Incident rate: {worst[2]:.2f}%")
print(f"Change: {worst[3]:+.2f} percentage points")
print(f"Failed-payment share: {old_failure:.2f}% -> {new_failure:.2f}%")
print(f"Report saved: {OUTPUT}")
