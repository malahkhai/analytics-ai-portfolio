"""Generate a reproducible synthetic ecommerce dataset for the portfolio case study."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "daily_ecommerce_metrics.csv"


def create_sample_data(path=OUT):
    rng = random.Random(42)
    start = date(2026, 8, 15)
    end = date(2026, 10, 23)
    channels = {
        "paid_search": (1250, 0.051, 155),
        "organic_search": (950, 0.043, 146),
        "email": (450, 0.071, 138),
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for days in range((end-start).days + 1):
        day = start + timedelta(days=days)
        weekend_multiplier = 0.83 if day.weekday() in (5, 6) else 1.0
        for channel, (base_sessions, base_cr, base_aov) in channels.items():
            sessions = int(base_sessions * weekend_multiplier * rng.uniform(0.96, 1.04))
            cr = base_cr * rng.uniform(0.96, 1.04)
            if channel == "paid_search" and day in (date(2026, 10, 13), date(2026, 10, 14)):
                cr *= 0.38  # Injected conversion-rate incident (known ground truth)
            if channel == "email" and day == date(2026, 10, 20):
                sessions = int(sessions * 0.37)  # Injected traffic incident
            orders = round(sessions * cr)
            revenue = round(orders * base_aov * rng.uniform(0.97, 1.03), 2)
            rows.append({"date": day.isoformat(), "channel": channel, "sessions": sessions,
                         "orders": orders, "revenue_eur": f"{revenue:.2f}"})
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "channel", "sessions", "orders", "revenue_eur"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(f"Generated {create_sample_data()} synthetic rows in {OUT}")
