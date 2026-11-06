# Owner-connected Outlook delivery

The public email dialog keeps the existing subject and report preview. A visitor enters one recipient address and clicks **Send report to my email**. Visitors never sign into Microsoft. The subject and body come from the selected report; arbitrary public messages, subjects, senders and recipient lists are not accepted.

## One-time owner setup

1. Register an application in Microsoft Entra that supports **personal Microsoft accounts**. Use your own application registration, not a third-party client ID.
2. Under Authentication, enable public client flows for local device-code authorization. No client secret is needed.
3. Add delegated Microsoft Graph `Mail.Send` and `User.Read` permissions. The MSAL sign-in also requests its standard offline access so it can silently renew access tokens. The intended account is `akinola.tunde@outlook.com`.
4. From `case-studies/01-signal-investigator`, activate the existing virtual environment, then run:

   ```bash
   python scripts/connect_outlook_sender.py --client-id YOUR_APPLICATION_CLIENT_ID
   ```

5. Complete Microsoft sign-in as the owner and consent to the stated permissions. The script verifies the mailbox through `/me`, then writes `.streamlit/outlook-secrets.toml` with owner-only file permissions. It never prints tokens.
6. Copy that TOML into the deployed app's **Settings → Secrets** in Streamlit Community Cloud. These secrets belong in the hosting settings, never in GitHub. Keep any existing app secrets. Restart the app after saving.
7. Request a report to an address you control. Microsoft Graph returning HTTP 202 means accepted for sending, not a delivery receipt; confirm Inbox/Junk and the owner's Sent Items.

Required secret names are `MAXIM_EMAIL_ENABLED`, `MICROSOFT_CLIENT_ID`, and `MICROSOFT_TOKEN_CACHE`. To disable sending, set `MAXIM_EMAIL_ENABLED = "0"`.

## Authorization and limits

The server holds an MSAL cache in private memory and silently refreshes tokens. Microsoft may revoke consent or expire authorization; if it does, the owner repeats setup and rotates the hosting secret. The initial token cache in hosting secrets is not rewritten automatically. Community Cloud restarts restore that initial seed, so this is not a permanent account connection or a durable token vault. For a larger deployment, use an encrypted persistent token store.

Each server process allows at most 20 messages per hour, one message every 10 seconds globally, and one report per recipient per 10 minutes. Limits are shared across visitor sessions, but reset on server restart and are not a distributed anti-abuse service. This is a low-volume portfolio sender. No recipient addresses are written to disk; transient delivery-limit state expires from memory. Requests are sent only on form submission, never while typing an address or loading a page.

The existing PDF/draft downloads remain available when authorization is absent, expired, or delivery fails. Public errors never include provider token responses or credentials.

References: [MSAL token acquisition](https://learn.microsoft.com/en-us/entra/msal/python/getting-started/acquiring-tokens), [Graph sendMail](https://learn.microsoft.com/en-us/graph/api/user-sendmail), [Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
