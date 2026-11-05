"""Explicitly authorized Microsoft Graph demo-mail delivery.

Nothing is sent on import or app load. Sending requires a verified delegated
Outlook token and the user's button click. The signed-in mailbox must match
EXPECTED_SENDER, preventing a forged From header.
"""
from __future__ import annotations

import re
from datetime import date

EXPECTED_SENDER = "akinola.tunde@outlook.com"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.Send", "User.Read"]


def validate_recipient(recipient: str) -> str:
    if not isinstance(recipient, str):
        raise ValueError("Recipient email is required")
    value = recipient.strip()
    if (len(value) > 254 or not re.fullmatch(r"[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value)
            or ".." in value):
        raise ValueError("Please enter one valid email address")
    return value


def compose_sample(row: dict, overview: str, financial: dict | None = None) -> tuple[str, str]:
    from src.dashboard_presentation import severity
    from src.interview_demo import is_synthetic
    from src.executive_report import decision, alert_reason, executive_headline

    if is_synthetic(row):
        financial = None  # Never present the real 2020-12-07 revenue as synthetic revenue.
    from src.financial_evidence import matching_financial_evidence
    financial = matching_financial_evidence(row, financial) if financial else None

    status = {"red": "ANOMALY", "yellow": "WATCHLIST", "green": "DAILY REVIEW", "unknown": "VERIFY DATA"}[severity(row)]
    day = date.fromisoformat(row["investigation_date"]).strftime("%d %b %Y")
    subject = f"[Maxim Demo] {'[SYNTHETIC INTERVIEW ALERT] ' if is_synthetic(row) else ''}{status} | {executive_headline(row)} | {day}"
    d = decision(row)
    revenue_section = (
        f"Recorded purchase revenue: ${financial['purchase_revenue_usd']:,.2f} USD\n"
        + (f"Revenue vs four matching-weekday baseline: ${financial['revenue_difference_usd']:+,.2f} USD (descriptive difference; not lost revenue)\n" if financial.get("revenue_difference_usd") is not None else "Revenue baseline comparison: not yet available\n")
    ) if financial else "Recorded purchase revenue: not available for this date\n"
    body = (
        ("SYNTHETIC RED ALERT — INTERVIEW DEMONSTRATION ONLY; NOT A REAL HISTORICAL INCIDENT\n" if is_synthetic(row) else "SAMPLE EXECUTIVE INVESTIGATION — HISTORICAL GA4-DERIVED CASE-STUDY DATA\n")
        + "Prepared by Maxim · AI Performance Investigation Analyst\n"
        + ("This simulation narrative was authored for the demo; Gemini did not generate a new investigation.\n\n" if is_synthetic(row) else "AI-generated findings have not been approved as verified causes.\n\n")
        + f"Reporting date: {row['investigation_date']}\n"
        f"Classification: {status}\n\n"
        f"EXECUTIVE SUMMARY\n{overview}\n\n"
        f"EVIDENCE\nSessions: {row['observed_sessions']:,} ({row['session_change_pct']:+.1f}% vs matching weekdays)\n"
        f"Purchase-session rate: {row['observed_purchase_rate_pct']:.2f}% ({row['purchase_rate_change_pct']:+.1f}% relative)\n"
        + revenue_section
        + f"Alert explanation: {alert_reason(row)}\n\n"
        + f"PROPOSED NEXT CHECK\n{d['action']}\n"
        + f"Suggested owner role (illustrative): {d['owner']}\n"
        + f"Reason: {d['why']}\n\n"
        + "Report status: Historical public data, for demonstration only.\n"
        + "This email is a sample; do not use as a live operational alert.\n"
    )
    return subject, body


def verify_graph_sender(access_token: str, http_client=None) -> str:
    if not access_token:
        raise PermissionError("Outlook account not connected")
    if http_client is None:
        import requests
        http_client = requests
    response = http_client.get(
        f"{GRAPH_BASE}/me",
        headers={"Authorization": f"Bearer {access_token}"}, timeout=15,
    )
    response.raise_for_status()
    identity = response.json()
    emails = {str(identity.get(k) or "").strip().lower() for k in ("mail", "userPrincipalName")}
    if EXPECTED_SENDER not in emails:
        raise PermissionError("The signed-in Microsoft account is not the approved Outlook sender")
    return EXPECTED_SENDER


def send_graph_email(access_token: str, recipient: str, subject: str, body: str, http_client=None) -> bool:
    recipient = validate_recipient(recipient)
    if not subject or not body:
        raise ValueError("Subject and body are required")
    if http_client is None:
        import requests
        http_client = requests
    verify_graph_sender(access_token, http_client)
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": recipient}}],
        },
        "saveToSentItems": True,
    }
    response = http_client.post(
        f"{GRAPH_BASE}/me/sendMail", json=payload,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    if response.status_code != 202:
        raise RuntimeError(f"Microsoft Graph returned unexpected status {response.status_code}")
    return True  # Accepted by Microsoft Graph, not a delivery receipt.


def begin_outlook_sign_in(client_id: str):
    if not client_id:
        raise ValueError("MICROSOFT_CLIENT_ID is required")
    import msal
    app = msal.PublicClientApplication(client_id, authority="https://login.microsoftonline.com/consumers")
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError("Could not start Microsoft sign-in")
    return app, flow


def complete_outlook_sign_in(app, flow):
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise PermissionError(result.get("error_description", "Microsoft sign-in was not completed"))
    token = result["access_token"]
    verify_graph_sender(token)
    return token
