# Dograh Voice Receptionist

Production AI voice receptionist built on **[Dograh](https://github.com/dograh-hq/dograh)** — the open-source, self-hostable alternative to Vapi & Retell — plus **Docker** and a small tools server.

**What it does:** answers calls as "Maya" (Pixalified receptionist), qualifies the caller, captures name/phone/interest, saves the lead via webhook, and confirms. Runs 100% on your own infra — no per-minute SaaS fees.

## Architecture

```
inbound/outbound call (Twilio etc.)
  -> Dograh (self-hosted, Docker) — STT -> LLM -> TTS, workflow engine
       -> webhook node -> tools/lead_server.py  (lead capture, /webhook/lead)
       -> QA node (call quality analysis)
  -> agent created programmatically via Dograh REST API (agent/create_agent.py)
```

## Quickstart

### 1. Self-host Dograh (official one-command install)

```bash
cd selfhost && ./start_docker.sh   # answer Y; first start takes 2-3 min
```

Open http://localhost:3010, create your account, and copy your **API key** from the dashboard — you'll need it below. No provider keys needed to start: Dograh ships its own LLM/TTS/STT stack (BYO providers anytime).

Or everything after this step in one go:

```bash
DOGRAH_API_KEY=dg_your_key ./setup.sh
```

### 2. Run the tools server (lead capture webhook)

```bash
cp .env.example .env   # fill in DOGRAH_API_KEY (from your Dograh dashboard/.env)
docker compose up --build
```

This starts the FastAPI lead server on `:8090`. Dograh's webhook node calls it when a lead is captured.

> **Lock it down:** set `WEBHOOK_SECRET` in your environment and add it as an `X-Webhook-Secret` custom header on Dograh's webhook node — otherwise anyone with the URL can POST fake leads.

> **Networking note:** the webhook URL must be reachable *from the Dograh containers*.
> Docker Desktop (Mac/Windows): `http://host.docker.internal:8090` (default).
> Linux: use your host LAN IP or the docker0 gateway (e.g. `http://172.17.0.1:8090`).

### 3. Create the agent

```bash
export DOGRAH_API_URL=http://localhost:3010/api/v1
export DOGRAH_API_KEY=dg_your_key
export TOOLS_PUBLIC_URL=http://host.docker.internal:8090
python3 agent/create_agent.py
```

This uploads `agent/workflow.json` (Maya receptionist: global brand voice → qualify + extract → save-lead webhook → confirm → QA → goodbye) via Dograh's `POST /api/v1/workflow/create/definition`.

### 4. Test it

- **Browser:** open the agent in Dograh's dashboard → Test Agent → Test Audio, talk to Maya.
- **Outbound call:** `AGENT_UUID=<uuid> TEST_PHONE=+91XXXXXXXXXX python3 scripts/test_call.py`
- **Telephony:** point your Twilio/Vonage number at `POST {DOGRAH_API_URL}/telephony/inbound/{workflow_id}`.

## Layout

| Path | What |
|---|---|
| `agent/workflow.json` | Maya receptionist workflow (schema-valid nodes/edges) |
| `agent/create_agent.py` | Uploads the workflow via Dograh REST API (stdlib only) |
| `tools/lead_server.py` | FastAPI webhook receiver — persists leads |
| `tools/Dockerfile` | Container for the tools server |
| `docker-compose.yaml` | Runs the tools server |
| `scripts/test_call.py` | Triggers an outbound test call |
| `.env.example` | All config in one place |

## Tests

```bash
python3 tests/test_lead_server.py   # webhook: stores leads, 400s garbage, secret gate
python3 tests/test_workflow.py      # workflow.json obeys Dograh's schema rules
python3 tests/test_api_scripts.py   # both API scripts hit the right endpoints (stub server)
```

## Notes

- Workflow schema follows Dograh's official `workflow-schema.md` (startCall/agentNode/webhook/qa/endCall, edges with natural-language conditions).
- `TOOLS_PUBLIC_URL` is injected into the webhook node at creation time — no hardcoded URLs in the workflow.
- Leads land in `tools/data/leads.json` (mounted volume) and are listable at `GET /leads`.
