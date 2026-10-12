#!/usr/bin/env python3
"""Create the Maya receptionist workflow on a Dograh instance via REST API.

Env:
  DOGRAH_API_URL    base URL, e.g. http://localhost:3010/api/v1 (self-hosted)
  DOGRAH_API_KEY    X-API-Key value (dg_...)
  TOOLS_PUBLIC_URL  tools-server URL reachable FROM the Dograh containers
                    (default http://host.docker.internal:8090)

Injects TOOLS_PUBLIC_URL into the webhook node, then POSTs
/api/v1/workflow/create/definition. stdlib only.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = os.environ.get("DOGRAH_API_URL", "http://localhost:3010/api/v1").rstrip("/")
KEY = os.environ.get("DOGRAH_API_KEY")
TOOLS_URL = os.environ.get("TOOLS_PUBLIC_URL", "http://host.docker.internal:8090").rstrip("/")

if not KEY:
    sys.exit("Set DOGRAH_API_KEY first (find it in your Dograh dashboard or .env).")

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "workflow.json")) as f:
    workflow = json.load(f)

# inject the tools-server URL into the webhook node (no hardcoded URLs in git)
workflow = json.loads(json.dumps(workflow).replace("__TOOLS_PUBLIC_URL__", TOOLS_URL))

payload = {
    "name": "Maya - Pixalified Voice Receptionist",
    "workflow_definition": workflow,
}
req = urllib.request.Request(
    f"{API}/workflow/create/definition",
    method="POST",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json", "X-API-Key": KEY},
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)
except urllib.error.HTTPError as e:
    sys.exit(f"Dograh API error {e.code}: {e.read().decode()[:500]}")

print(json.dumps(body, indent=2)[:2000])
print("\nAgent created. Test it in the Dograh dashboard (Test Audio) or via scripts/test_call.py")
