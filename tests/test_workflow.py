"""Ponytail check: workflow.json obeys Dograh's validation rules."""
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
wf = json.load(open(os.path.join(here, "..", "agent", "workflow.json")))
nodes, edges = wf["nodes"], wf["edges"]

ids = [n["id"] for n in nodes]
assert len(ids) == len(set(ids)), "duplicate node ids"

entry = [n for n in nodes if n["type"] in ("startCall", "trigger")]
assert len(entry) == 1, f"need exactly one entry node, got {len(entry)}"

for n in nodes:
    assert n["type"] in ("startCall", "endCall", "agentNode", "globalNode",
                         "trigger", "webhook", "qa"), f"unknown type {n['type']}"
    if n["type"] not in ("trigger", "webhook", "qa"):
        assert n["data"].get("prompt"), f"node {n['id']} missing prompt"
    assert n["data"].get("name"), f"node {n['id']} missing name"

for e in edges:
    assert e["source"] in ids and e["target"] in ids, f"bad edge {e['id']}"
    assert e["data"].get("condition"), f"edge {e['id']} missing condition"

# the lead-capture path exists: qualify -> webhook -> confirm
targets = {(e["source"], e["target"]) for e in edges}
assert ("qualify-1", "webhook-1") in targets
assert ("webhook-1", "confirm-1") in targets

print(f"test_workflow OK ({len(nodes)} nodes, {len(edges)} edges)")
