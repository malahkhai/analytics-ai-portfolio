
"""Prepare BigQuery GA4 metrics for analytics investigation."""

from datetime import date


def adapt_ga4_records(records):
    """Validate and normalize daily GA4 ecommerce records."""

    prepared = []
    seen_dates = set()

    for record in records:
        day = date.fromisoformat(record["event_day"])

        sessions = int(record["sessions"])
        purchasing_sessions = int(record["purchasing_sessions"])
        purchase_events = int(record["purchase_events"])
        reported_rate = float(
            record["session_purchase_rate_pct"]
        )

        # Check for duplicate dates.
        if day in seen_dates:
            raise ValueError(f"Duplicate GA4 date: {day}")

        seen_dates.add(day)

        # Validate metrics before using them.
        if sessions <= 0:
            raise ValueError(f"Invalid sessions on {day}")

        if not 0 <= purchasing_sessions <= sessions:
            raise ValueError(
                f"Invalid purchasing sessions on {day}"
            )

        if purchase_events < purchasing_sessions:
            raise ValueError(
                f"Purchase event count inconsistent on {day}"
            )

        expected_rate = round(
            purchasing_sessions / sessions * 100,
            2
        )

        if (
            not 0 <= reported_rate <= 100
            or abs(reported_rate - expected_rate) > 0.011
        ):
            raise ValueError(
                f"Inconsistent purchase rate on {day}"
            )


        prepared_row = {
            "date": day,
            "scope": "all_channels_aggregated",
            "sessions": sessions,
            "purchase_events": purchase_events,
            "purchasing_sessions": purchasing_sessions,
            "session_purchase_rate_pct": reported_rate,
        }

        # Preserve and validate financial metrics when supplied.
        financial_fields = (
            "purchase_events_with_revenue",
            "purchase_revenue_usd",
            "revenue_evidence_type",
        )

        if any(key in record for key in financial_fields):
            if not all(key in record for key in financial_fields):
                raise ValueError(f"Incomplete revenue evidence on {day}")

            coverage = int(record["purchase_events_with_revenue"])
            revenue = float(record["purchase_revenue_usd"])
            evidence_type = record["revenue_evidence_type"]

            if not 0 <= coverage <= purchase_events:
                raise ValueError(f"Invalid revenue coverage on {day}")

            if not 0 <= revenue < float("inf"):
                raise ValueError(f"Invalid revenue amount on {day}")

            if evidence_type not in ("recorded", "modeled"):
                raise ValueError(f"Invalid revenue evidence type on {day}")

            prepared_row.update({
                "purchase_events_with_revenue": coverage,
                "purchase_revenue_usd": revenue,
                "revenue_evidence_type": evidence_type,
            })

        prepared.append(prepared_row)


    return sorted(prepared, key=lambda row: row["date"])
