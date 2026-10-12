#!/usr/bin/env python3
"""Trigger an outbound test call via the Dograh REST API.

Env:
  DOGRAH_API_URL  base URL, e.g. http://localhost:3010/api/v1
  DOGRAH_API_KEY  X-API-Key value (dg_...)
  AGENT_UUID      public agent UUID from the Dograh dashboard
  TEST_PHONE      destination number in E.164 format, e.g. +91XXXXXXXXXX
"""
import json
import os
import sys
import urllib.request

API = os.environ.get("DOGRAH_API_URL", "http://localhost:3010/api/v1").rstrip("/")
KEY = os.environ.get("DOGRAH_API_KEY")
AGENT_UUID = os.environ.get("AGENT_UUID")
PHONE = os.environ.get("TEST_PHONE")

missing = [k for k, v in {
    "DOGRAH_API_KEY": KEY, "AGENT_UUID": AGENT_UUID, "TEST_PHONE": PHONE,
}.items() if not v]
if missing:
    sys.exit(f"Missing env: {', '.join(missing)}")

payload = {
    "phone_number": PHONE,
    "initial_context": {"customer_name": "Test Caller"},
}
req = urllib.request.Request(
    f"{API}/public/agent/{AGENT_UUID}",
    method="POST",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "X-API-Key": KEY},
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(json.dumps(json.load(resp), indent=2)[:2000])
except urllib.error.HTTPError as e:
    sys.exit(f"Dograh API error {e.code}: {e.read().decode()[:500]}")
