"""Webhook receiver for the Dograh voice receptionist.

Dograh's webhook node POSTs here when the agent captures a lead.
Persists to data/leads.json; list via GET /leads.
"""
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
    rows = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE) as f:
                rows = json.load(f)
        except (json.JSONDecodeError, OSError):
            rows = []
    record["received_at"] = datetime.now(timezone.utc).isoformat()
    rows.append(record)
    with open(LEADS_FILE, "w") as f:
        json.dump(rows, f, indent=2)


@app.post("/webhook/lead")
async def lead(req: Request):
    data = await req.json()
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
