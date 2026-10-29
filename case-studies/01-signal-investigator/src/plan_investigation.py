
"""Create an investigation plan from an anomaly alert."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "outputs" / "investigations.json"
output = ROOT / "outputs" / "first_investigation_plan.md"

# Step 1: Read the alerts detected by our first script.
alerts = json.loads(source.read_text(encoding="utf-8"))["alerts"]

# Step 2: Select the October 13 paid search incident.
alert = next(
    (item for item in alerts
     if item["date"] == "2026-10-13"
     and item["channel"] == "paid_search"),
    None,
)

if alert is None:
    raise SystemExit("Alert not found. Run: python3 -m src.detect")

# Step 3: Define hypotheses and the evidence needed.
hypotheses = [
    (
        "Checkout or payment issue",
        "Review funnel drop-offs, checkout errors and payment logs."
    ),
    (
        "Purchase tracking issue",
        "Compare GA4 purchase events against backend orders."
    ),
    (
        "Lower-quality paid search traffic",
        "Compare campaigns, search terms, devices and audiences."
    ),
    (
        "Product availability issue",
        "Check stock levels for popular products and landing pages."
    ),
]

# Step 4: Assemble our investigation report.
lines = [
    "# Investigation plan — Paid Search — 2026-10-13",
    "",
    "## Observed evidence",
    f"- Sessions: {alert['observed_sessions']:,}",
    f"- Orders: {alert['observed_orders']:,}",
    f"- Observed CR: {alert['observed_conversion_rate_pct']:.2f}%",
    f"- Historical CR: {alert['baseline_conversion_rate_pct']:.2f}%",
    f"- Relative CR change: {alert['change_vs_baseline_pct']:.1f}%",
    "",
    "## Hypotheses to test (not verified)",
]

for index, (hypothesis, check) in enumerate(hypotheses, start=1):
    lines.append(f"{index}. **{hypothesis}** — {check}")

lines.extend([
    "",
    "## Current conclusion",
    "Root cause not established. Additional funnel, tracking, "
    "campaign and stock data are needed.",
    "",
    "*Dataset: synthetic demo. No live GA4 or backend data used.*",
])

# Step 5: Save the report as a Markdown file.
output.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Investigation plan saved: {output}")
