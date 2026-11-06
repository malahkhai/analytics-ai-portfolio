"""Server-side owner connection for public report delivery."""
from src.email_delivery import EXPECTED_SENDER, SCOPES, validate_recipient, send_graph_email


class OutlookSender:
    """Owner-authorized sender shared by the server, never by a visitor session.

    The owner seeds a serialized MSAL cache in hosting secrets. MSAL renews
    access tokens silently; no token or Microsoft login is exposed to visitors.
    Limits apply across all sessions in this server process. Microsoft can
    revoke consent, so configuration does not imply permanent authorization.
    """

    def __init__(self, client_id: str, serialized_cache: str, *, app=None, clock=None):
        import threading
        import time
        if not client_id or not serialized_cache:
            raise ValueError("Owner sender authorization is required")
        if app is None:
            import msal
            cache = msal.SerializableTokenCache()
            try:
                cache.deserialize(serialized_cache)
            except (ValueError, TypeError):
                raise ValueError("Owner sender authorization is invalid") from None
            app = msal.PublicClientApplication(
                client_id, authority="https://login.microsoftonline.com/consumers",
                token_cache=cache,
            )
        self._app = app
        self._lock = threading.Lock()
        self._clock = clock or time.monotonic
        self._sent = []
        self._recipient_sent = {}

    def _access_token(self) -> str:
        accounts = [account for account in self._app.get_accounts()
                    if str(account.get("username", "")).lower() == EXPECTED_SENDER]
        if not accounts:
            raise PermissionError("Sender authorization needs to be renewed by the dashboard owner")
        result = self._app.acquire_token_silent(SCOPES, account=accounts[0])
        if not result or not result.get("access_token"):
            # Never expose provider error_description, caches or credentials in UI.
            raise PermissionError("Sender authorization needs to be renewed by the dashboard owner")
        return result["access_token"]

    def send(self, recipient: str, subject: str, body: str, *, http_client=None) -> bool:
        """Send only the server-generated report, after an explicit visitor click."""
        recipient = validate_recipient(recipient)
        key = recipient.lower()
        with self._lock:
            now = self._clock()
            self._sent = [stamp for stamp in self._sent if now - stamp < 3600]
            self._recipient_sent = {address: stamp for address, stamp in self._recipient_sent.items()
                                    if now - stamp < 600}
            if key in self._recipient_sent:
                raise ValueError("A report was recently sent to this address. Please wait 10 minutes.")
            if self._sent and now - self._sent[-1] < 10:
                raise ValueError("Please wait a few seconds before requesting another email.")
            if len(self._sent) >= 20:
                raise ValueError("The report email limit has been reached. Please download the PDF instead.")
            token = self._access_token()
            sent = send_graph_email(token, recipient, subject, body, http_client)
            if sent:
                self._sent.append(now)
                self._recipient_sent[key] = now
            return sent
