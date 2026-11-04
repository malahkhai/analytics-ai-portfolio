
"""Signal Investigator: first tool-using Gemini agent."""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.ga4_comparison_tool import (
    compare_ga4_performance as lookup_ga4_comparison
)


ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "outputs" / "ga4_diagnostics.json"
OUTPUT = ROOT / "outputs" / "ga4_tool_agent_report.md"

MODEL = "gemini-3.8-flash"

# Track actual Python tool executions.
TOOL_CALLS = []


def get_ga4_diagnostic(day: str) -> dict:
    """Retrieve verified GA4 performance evidence for one date.

    Args:
        day: Date to investigate, in YYYY-MM-DD format.

    Returns:
        The stored diagnostic evidence or an error status.
    """

    TOOL_CALLS.append(day)
    print(f"[TOOL CALLED] get_ga4_diagnostic(day={day})")

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return {
            "status": "invalid_date",
            "message": "Use YYYY-MM-DD format.",
        }

    # Read only our existing local evidence file.
    with DIAGNOSTICS.open(encoding="utf-8") as file:
        report = json.load(file)

    evidence = next(
        (
            item for item in report["evaluations"]
            if item["date"] == day
        ),
        None,
    )

    if evidence is None:
        return {
            "status": "not_found",
            "date": day,
            "message": "No baseline-ready diagnostic exists.",
        }


    # Evaluate the actual conversion alert conditions.
    sessions_met = evidence["observed_sessions"] >= 150

    rate_change = evidence["purchase_rate_change_pct"]
    rate_drop_met = (
        rate_change is not None
        and rate_change <= -35
    )

    shortfall_met = (
        evidence["estimated_purchase_session_gap"] >= 15
    )

    return {
        "status": "ok",
        "source": report["source"],
        "evidence": evidence,
        "method": "Four previous matching weekdays",
        "conversion_alert_rule": {
            "minimum_sessions": 150,
            "minimum_relative_rate_drop_pct": 35,
            "minimum_purchase_session_gap": 15,
            "conditions": {
                "sessions_met": sessions_met,
                "rate_drop_met": rate_drop_met,
                "shortfall_met": shortfall_met,
            },
            "alert_triggered": (
                sessions_met
                and rate_drop_met
                and shortfall_met
            ),
        },
    }


# Track calls to our second analytical tool.
COMPARISON_CALLS = []


def compare_ga4_performance(day: str) -> dict:
    """Compare a date with other baseline-ready GA4 dates.

    Args:
        day: Date to compare in YYYY-MM-DD format.

    Returns:
        Historical rankings and performance comparisons.
    """

    COMPARISON_CALLS.append(day)

    print(
        f"[TOOL CALLED] "
        f"compare_ga4_performance(day={day})"
    )

    return lookup_ga4_comparison(day)


def main():
    load_dotenv(dotenv_path=ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)

    try:

        chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                tools=[get_ga4_diagnostic,
                       compare_ga4_performance],
                automatic_function_calling=(
                    types.AutomaticFunctionCallingConfig(
                        maximum_remote_calls=4
                    )
                ),
                temperature=0,
            ),
        )

        response = chat.send_message(
            message="""
You are Signal Investigator, an AI analytics agent.

Investigate ecommerce performance on 2020-12-07.

Answer these two business questions:

1. Why did December 7 not trigger a
   conversion-rate anomaly alert?

2. Did December 7 experience both the
   largest session growth and the largest
   purchase-rate decline among all dates
   eligible for historical comparison?

Use the available analytical tools to verify
the alert conditions and historical rankings.

Do not guess at missing information.

Your final investigation must contain:

- Executive summary
- Alert-condition assessment
- Historical performance ranking
- Three plausible explanations worth testing
- Most useful next analytical check
- Missing evidence and limitations

Rules:
- Use only evidence returned by the tools.
- Do not invent metrics, revenue or orders.
- Purchasing sessions are not orders.
- Estimated gaps are not confirmed lost sales.
- Do not claim a root cause has been established.
- Do not introduce statistical testing that
  was not performed.
- Clearly distinguish evidence from hypotheses
"""
        )

    finally:
        client.close()

    if "2020-12-07" not in TOOL_CALLS:
        raise RuntimeError(
            "Gemini did not execute the required tool."
        )

    if "2020-12-07" not in COMPARISON_CALLS:
        raise RuntimeError(
            "Gemini did not execute the historical comparison tool."
        )


    if not response.text:
        raise RuntimeError("Gemini returned no report.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        response.text,
        encoding="utf-8",
    )

    print("\nTOOL-USING AI INVESTIGATION\n")
    print(response.text)

    print(f"\nDiagnostic tool calls: {len(TOOL_CALLS)}")
    print(f"Comparison tool calls: {len(COMPARISON_CALLS)}")
    print(f"Report saved: {OUTPUT}")


if __name__ == "__main__":
    main()
