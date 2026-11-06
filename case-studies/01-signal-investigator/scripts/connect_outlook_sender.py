"""Run locally as the mailbox owner; never run in the public Streamlit app.

Writes owner-only, gitignored secrets. No tokens are printed. Copy the generated
TOML to Streamlit Community Cloud's private Secrets settings after sign-in.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.email_delivery import EXPECTED_SENDER, SCOPES, verify_graph_sender


def main():
    parser = argparse.ArgumentParser(description="Authorize Maxim's Outlook sender")
    parser.add_argument("--client-id", required=True, help="Your Microsoft app registration Application (client) ID")
    args = parser.parse_args()
    import msal
    cache = msal.SerializableTokenCache()
    app = msal.PublicClientApplication(
        args.client_id, authority="https://login.microsoftonline.com/consumers", token_cache=cache,
    )
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise SystemExit("Microsoft could not start sign-in. Check the application ID and public-client configuration.")
    print(flow["message"])
    print(f"Sign in as {EXPECTED_SENDER}; approve the sender permission for your own app.")
    result = app.acquire_token_by_device_flow(flow)
    if not result.get("access_token"):
        raise SystemExit("Authorization did not complete. No sender secrets were saved.")
    verify_graph_sender(result["access_token"])
    target = ROOT / ".streamlit" / "outlook-secrets.toml"
    target.parent.mkdir(exist_ok=True)
    content = (
        'MAXIM_EMAIL_ENABLED = "1"\n'
        f'MICROSOFT_CLIENT_ID = {json.dumps(args.client_id)}\n'
        f'MICROSOFT_TOKEN_CACHE = {json.dumps(cache.serialize())}\n'
    )
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(content)
    print(f"Sender verified. Owner-only secrets saved to {target}")
    print("Copy this file into your app's private Streamlit Secrets settings. Never commit or share it.")


if __name__ == "__main__":
    main()
