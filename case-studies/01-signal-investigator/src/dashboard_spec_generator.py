
"""Gemini-generated, validated dashboard specifications."""

import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "outputs" / "ga4_executive_reporting.json"
MODEL = "gemini-3.8-flash"
TARGET_DATE = "2020-12-07"


class DashboardSpec(BaseModel):
    headline: str = Field(min_length=8, max_length=120)

    kpis: list[Literal[
        "observed_sessions",
        "observed_purchase_rate_pct",
        "session_change_pct",
        "purchase_rate_change_pct",
        "estimated_purchase_session_gap",
    ]] = Field(min_length=2, max_length=4)

    charts: list[Literal[
        "sessions_vs_baseline",
        "purchase_rate_vs_baseline",
        "session_change_trend",
        "purchase_rate_change_trend",
    ]] = Field(min_length=1, max_length=3)

    sections: list[Literal[
        "executive_summary",
        "alert_explanation",
        "hypotheses",
        "recommended_checks",
    ]] = Field(default_factory=list)


CHART_FIELDS = {
    "sessions_vs_baseline": [
        "observed_sessions", "baseline_sessions"
    ],
    "purchase_rate_vs_baseline": [
        "observed_purchase_rate_pct",
        "baseline_purchase_rate_pct",
    ],
    "session_change_trend": ["session_change_pct"],
    "purchase_rate_change_trend": [
        "purchase_rate_change_pct"
    ],
}

SECTION_FIELDS = {
    "executive_summary": "executive_summary",
    "alert_explanation": "why_no_alert",
    "hypotheses": "hypotheses_json",
    "recommended_checks": "recommended_checks_json",
}


def validate_spec(spec, rows, selected):
    """Reject unsupported or unavailable dashboard elements."""

    for group in (spec.kpis, spec.charts, spec.sections):
        if len(group) != len(set(group)):
            raise ValueError("Duplicate dashboard component.")

    for metric in spec.kpis:
        if selected.get(metric) is None:
            raise ValueError(f"Unavailable KPI: {metric}")

    for chart in spec.charts:
        fields = CHART_FIELDS[chart]

        if any(
            row.get(field) is None
            for row in rows
            for field in fields
        ):
            raise ValueError(f"Unavailable chart: {chart}")

    for section in spec.sections:
        field = SECTION_FIELDS[section]

        if (
            not selected.get("has_ai_investigation")
            or not selected.get(field)
        ):
            raise ValueError(
                f"Unavailable AI section: {section}"
            )

    return spec


def main():
    load_dotenv(dotenv_path=ROOT / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    rows = json.loads(REPORT.read_text(encoding="utf-8"))

    selected = next(
        (
            row for row in rows
            if row["investigation_date"] == TARGET_DATE
        ),
        None,
    )

    if selected is None:
        raise ValueError("Investigation date not found.")

    evidence = {
        "investigation_date": TARGET_DATE,
        "alert_status": selected["alert_status"],
        "has_ai_investigation": selected["has_ai_investigation"],
        "metrics": {
            metric: selected[metric]
            for metric in [
                "observed_sessions",
                "session_change_pct",
                "observed_purchase_rate_pct",
                "purchase_rate_change_pct",
                "estimated_purchase_session_gap",
            ]
        },
        "available_ai_sections": [
            section
            for section, field in SECTION_FIELDS.items()
            if selected["has_ai_investigation"]
            and selected.get(field)
        ],
    }

    prompt = (
        "You are designing an executive analytics dashboard. "
        "Select the most useful KPIs, charts, and investigation "
        "sections for this evidence. Prioritize explaining "
        "the business performance change. "
        "Use only components permitted by the output schema. "
        "Do not invent metrics or causes. "
        "Keep the headline short and descriptive, without "
        "numerical claims. "
        "Do not select AI sections unless listed as available. "
        "This is a historical demonstration dataset.\n\n"
        + json.dumps(evidence, indent=2)
    )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DashboardSpec,
            temperature=0,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned no dashboard specification.")

    spec = DashboardSpec.model_validate_json(response.text)
    validate_spec(spec, rows, selected)

    output = {
        "investigation_date": TARGET_DATE,
        "generated_by": MODEL,
        "factual_review_status": selected["factual_review_status"],
        "dashboard_spec": spec.model_dump(),
    }

    destination = (
        ROOT / "outputs" /
        f"ga4_dashboard_spec_{TARGET_DATE}.json"
    )

    destination.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print("\nGEMINI DASHBOARD SPECIFICATION")
    print(json.dumps(output, indent=2))
    print(f"\nSaved: {destination}")


if __name__ == "__main__":
    main()
