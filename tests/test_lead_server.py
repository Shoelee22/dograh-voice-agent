"""Ponytail check: the lead webhook never loses a lead and rejects garbage."""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["DATA_DIR"] = tmp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from fastapi.testclient import TestClient  # noqa: E402
import lead_server  # noqa: E402

c = TestClient(lead_server.app)

# happy path: lead stored with timestamp
r = c.post("/webhook/lead", json={"caller_name": "Asha", "caller_phone": "+911234",
                                  "interest": "website"})
assert r.status_code == 200 and r.json()["ok"], r.text
leads = c.get("/leads").json()
assert len(leads) == 1 and leads[0]["name"] == "Asha" and "received_at" in leads[0], leads

# garbage in -> 400, nothing stored
r = c.post("/webhook/lead", content=b"not json",
           headers={"content-type": "application/json"})
assert r.status_code == 400, r.status_code
r = c.post("/webhook/lead", json=["a", "list"])
assert r.status_code == 400, r.status_code
assert len(c.get("/leads").json()) == 1

# empty object doesn't crash
r = c.post("/webhook/lead", json={})
assert r.status_code == 200
assert len(c.get("/leads").json()) == 2

# secret gate: wrong/missing -> 401, correct -> 200
os.environ["WEBHOOK_SECRET"] = "s3cr3t"
assert c.post("/webhook/lead", json={}).status_code == 401
assert c.post("/webhook/lead", json={}, headers={"x-webhook-secret": "nope"}).status_code == 401
r = c.post("/webhook/lead", json={"caller_name": "Dev"},
           headers={"x-webhook-secret": "s3cr3t"})
assert r.status_code == 200, r.status_code
del os.environ["WEBHOOK_SECRET"]
assert c.get("/health").json() == {"ok": True}

print("test_lead_server OK")
