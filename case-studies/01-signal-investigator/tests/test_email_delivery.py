import unittest
from src.email_delivery import validate_recipient, compose_sample, verify_graph_sender, send_graph_email


class Response:
    def __init__(self, data=None, status_code=200):
        self.data = data or {}
        self.status_code = status_code
    def json(self): return self.data
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP failure")


class FakeHttp:
    def __init__(self, sender="akinola.tunde@outlook.com"):
        self.sender = sender
        self.posts = []
    def get(self, url, **kwargs):
        return Response({"mail": self.sender})
    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return Response(status_code=202)


class EmailTests(unittest.TestCase):
    def test_valid_recipient(self):
        self.assertEqual(validate_recipient(" test@example.com "), "test@example.com")
    def test_reject_multiple_or_injected_recipients(self):
        for bad in ("test@example.com,other@example.com", "evil\n@example.com", "none", ""):
            with self.assertRaises(ValueError): validate_recipient(bad)
    def test_signed_in_sender_required(self):
        with self.assertRaises(PermissionError):
            verify_graph_sender("token", FakeHttp("someone@outlook.com"))
    def test_no_send_if_wrong_sender(self):
        http = FakeHttp("somebody@example.org")
        with self.assertRaises(PermissionError):
            send_graph_email("token", "test@example.com", "Subject", "Body", http)
        self.assertEqual(http.posts, [])
    def test_send_requires_explicit_call(self):
        http = FakeHttp()
        self.assertTrue(send_graph_email("token", "test@example.com", "Subject", "Body", http))
        self.assertEqual(len(http.posts), 1)
        payload = http.posts[0][1]["json"]
        self.assertEqual(payload["message"]["toRecipients"][0]["emailAddress"]["address"], "test@example.com")
        self.assertNotIn("from", payload["message"])
    def test_email_draft_contains_real_vs_unavailable_finance(self):
        row = {"investigation_date": "2020-12-07", "alert_status": "no_qualifying_anomaly", "alert_types": [],
               "observed_sessions": 5461, "session_change_pct": 42, "observed_purchase_rate_pct": 1.67,
               "purchase_rate_change_pct": -14.5, "estimated_purchase_session_gap": 15.5,
               "has_ai_investigation": False}
        subj, body = compose_sample(row, "Executive check", {"purchase_revenue_usd": 8472, "revenue_difference_usd": None})
        self.assertIn("[Maxim Demo]", subj)
        self.assertIn("$8,472.00", body)
        self.assertIn("not yet available", body)
        self.assertIn("historical", body.lower())


if __name__ == "__main__":
    unittest.main()


class SenderCacheTests(unittest.TestCase):
    class App:
        def __init__(self, username="akinola.tunde@outlook.com", token="owner-token"):
            self.username, self.token = username, token
            self.calls = []
        def get_accounts(self):
            return [{"username": self.username}]
        def acquire_token_silent(self, scopes, account):
            self.calls.append((scopes, account))
            return {"access_token": self.token} if self.token else None

    def sender(self, app=None):
        from src.outlook_sender import OutlookSender
        return OutlookSender("client-id", "owner-cache", app=app or self.App(), clock=lambda: 1000)

    def test_visitor_does_not_need_microsoft_login(self):
        app = self.App()
        http = FakeHttp()
        self.assertTrue(self.sender(app).send("visitor@example.com", "Report", "Evidence", http_client=http))
        self.assertEqual(len(app.calls), 1)
        self.assertEqual(len(http.posts), 1)
        self.assertEqual(http.posts[0][1]["json"]["message"]["body"]["content"], "Evidence")

    def test_wrong_owner_cache_never_sends(self):
        http = FakeHttp()
        with self.assertRaises(PermissionError):
            self.sender(self.App(username="other@example.com")).send("visitor@example.com", "Report", "Evidence", http_client=http)
        self.assertEqual(http.posts, [])

    def test_expired_consent_never_sends(self):
        http = FakeHttp()
        with self.assertRaises(PermissionError):
            self.sender(self.App(token=None)).send("visitor@example.com", "Report", "Evidence", http_client=http)
        self.assertEqual(http.posts, [])

    def test_shared_recipient_limit_blocks_duplicate_delivery(self):
        sender, http = self.sender(), FakeHttp()
        sender.send("visitor@example.com", "Report", "Evidence", http_client=http)
        with self.assertRaises(ValueError):
            sender.send("VISITOR@example.com", "Report", "Evidence", http_client=http)
        self.assertEqual(len(http.posts), 1)
