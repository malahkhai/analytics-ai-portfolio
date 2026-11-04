
"""Generate a Gemini investigation from verified GA4 evidence."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "outputs" / "ga4_diagnostics.json"

OUTPUT = (
    ROOT / "outputs" /
    "ga4_ai_investigation_2020-12-07.md"
)

TARGET_DATE = "2020-12-07"


def main():

    # Load our local Gemini API key.
    load_dotenv(dotenv_path=ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    # Read evidence created by our Python analytics engine.
    with INPUT.open(encoding="utf-8") as file:
        report = json.load(file)

    # Select the December 7 investigation.
    evidence = next(
        (
            item for item in report["evaluations"]
            if item["date"] == TARGET_DATE
        ),
        None,
    )

    if evidence is None:
        raise ValueError(
            f"No diagnostic evidence for {TARGET_DATE}"
        )

    context = {
        "source": report["source"],
        "evidence": evidence,
        "detection_rules": {
            "minimum_rate_decline_pct": 35,
            "minimum_expected_purchase_session_gap": 15,
            "minimum_sessions": 150,
            "method": "Four previous matching weekdays",
            "statistical_significance_test": False,
        },
    }

    prompt = f"""
You are a Senior Digital Analytics Investigation Analyst.

Your responsibility is to interpret verified analytics
evidence and propose useful next investigation steps.

EVIDENCE:
{json.dumps(context, indent=2)}

INSTRUCTIONS:

1. Explain what actually changed in plain English.

2. Explain why the result did not trigger an
   anomaly alert.

3. Propose three plausible hypotheses that could
   explain the performance change.

4. For each hypothesis, identify what additional
   data would be needed to test it.

5. Recommend the three most useful next
   analytical checks, in priority order.

STRICT RULES:

- Use only the supplied evidence for factual claims.
- Do not invent revenue, orders or channel performance.
- Purchasing sessions are not the same as orders.
- Do not claim that any hypothesis is proven.
- Do not claim statistical significance.
- Distinguish relative percent changes from
  percentage-point changes.
- Treat the estimated shortfall as a baseline
  comparison, not confirmed lost sales.
- Clearly identify missing evidence.
- This is historical, aggregated GA4 sample data.

FORMAT:

# Executive Summary
# What the Data Shows
# Why No Alert Was Triggered
# Investigation Hypotheses
# Recommended Next Checks
# Limitations

Keep the report concise and suitable for a
Marketing Analytics Director.
"""

    print("Sending verified GA4 evidence to Gemini...")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        result = response.text

        if not result:
            raise RuntimeError(
                "Gemini returned no text."
            )

    finally:
        client.close()

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        result,
        encoding="utf-8",
    )

    print("\nAI INVESTIGATION REPORT\n")
    print(result)

    print(f"\nReport saved: {OUTPUT}")


if __name__ == "__main__":
    main()
