"""Ponytail check: both API scripts hit the right endpoints with the right shape.

Runs each script as a subprocess against a stub HTTP server that records
the request — no live Dograh instance needed.
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

captured = {}


class Stub(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        captured.update(
            path=self.path,
            api_key=self.headers.get("X-API-Key"),
            body=json.loads(self.rfile.read(n) or b"{}"),
        )
        out = json.dumps({"uuid": "abc-123", "id": 7}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


srv = HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]
here = os.path.dirname(os.path.abspath(__file__))

# --- create_agent.py ---
env = dict(os.environ,
           DOGRAH_API_URL=f"http://127.0.0.1:{port}/api/v1",
           DOGRAH_API_KEY="dg_testkey",
           TOOLS_PUBLIC_URL="http://tools:8090")
p = subprocess.run([sys.executable, os.path.join(here, "..", "agent", "create_agent.py")],
                   capture_output=True, text=True, env=env, timeout=30)
assert p.returncode == 0, p.stderr
assert captured["path"] == "/api/v1/workflow/create/definition", captured
assert captured["api_key"] == "dg_testkey", captured
assert captured["body"]["name"].startswith("Maya"), captured["body"]
dump = json.dumps(captured["body"]["workflow_definition"])
assert "__TOOLS_PUBLIC_URL__" not in dump, "webhook URL placeholder not replaced"
assert "http://tools:8090/webhook/lead" in dump

# --- test_call.py ---
captured.clear()
env = dict(os.environ,
           DOGRAH_API_URL=f"http://127.0.0.1:{port}/api/v1",
           DOGRAH_API_KEY="dg_testkey",
           AGENT_UUID="uuid-999",
           TEST_PHONE="+911234567890")
p = subprocess.run([sys.executable, os.path.join(here, "..", "scripts", "test_call.py")],
                   capture_output=True, text=True, env=env, timeout=30)
assert p.returncode == 0, p.stderr
assert captured["path"] == "/api/v1/public/agent/uuid-999", captured
assert captured["body"]["phone_number"] == "+911234567890", captured["body"]

# --- missing env fails loud, not silent ---
p = subprocess.run([sys.executable, os.path.join(here, "..", "scripts", "test_call.py")],
                   capture_output=True, text=True,
                   env={"PATH": os.environ["PATH"]}, timeout=30)
assert p.returncode != 0 and "Missing env" in p.stderr, (p.returncode, p.stderr)

srv.shutdown()
print("test_api_scripts OK")
