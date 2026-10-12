"""Webhook receiver for the Dograh voice receptionist.

Dograh's webhook node POSTs here when the agent captures a lead.
Persists to data/leads.json; list via GET /leads.

Security: set WEBHOOK_SECRET and Dograh must send it as the
X-Webhook-Secret header (webhook node -> custom headers). Unset = open.
"""
import fcntl
import json
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE)
os.makedirs(DATA_DIR, exist_ok=True)
LEADS_FILE = os.path.join(DATA_DIR, "leads.json")

app = FastAPI(title="Dograh Voice Agent Tools")


def append_lead(record: dict) -> None:
    record["received_at"] = datetime.now(timezone.utc).isoformat()
    with open(LEADS_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # two webhooks at once must not lose a lead
        try:
            f.seek(0)
            try:
                rows = json.load(f)
            except (json.JSONDecodeError, OSError):
                rows = []
            rows.append(record)
            f.seek(0)
            f.truncate()
            json.dump(rows, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


@app.post("/webhook/lead")
async def lead(req: Request):
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if secret and req.headers.get("x-webhook-secret") != secret:
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        data = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "invalid JSON"}, status_code=400)
    if not isinstance(data, dict):
        return JSONResponse({"ok": False, "error": "body must be a JSON object"},
                            status_code=400)
    append_lead({
        "name": data.get("caller_name") or data.get("name"),
        "phone": data.get("caller_phone") or data.get("phone"),
        "interest": data.get("interest"),
        "wants_human": data.get("wants_human"),
        "transcript": data.get("transcript"),
        "call_id": data.get("call_id"),
    })
    return JSONResponse({"ok": True})


@app.get("/leads")
def leads():
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE) as f:
            return json.load(f)
    return []


@app.get("/health")
def health():
    return {"ok": True}
