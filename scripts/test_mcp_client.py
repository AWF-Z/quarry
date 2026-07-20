#!/usr/bin/env python3
"""Dependency-free checks for the public Quarry MCP bridge."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("quarry_mcp", ROOT / "client/quarry_mcp.py")
CLIENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT)


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


class ClientTests(unittest.TestCase):
    def test_initialize_and_tool_schema(self):
        response = CLIENT.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                  "params": {"protocolVersion": "test-version"}})
        self.assertEqual(response["result"]["protocolVersion"], "test-version")
        tools = CLIENT.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools],
                         ["quarry_start", "quarry_submit", "quarry_finalize", "quarry_artifact"])
        instructions = response["result"]["instructions"]
        self.assertIn("Never create", instructions)
        self.assertIn("service mints", instructions)
        self.assertIn("Quarry Skill Only", instructions)

    def test_v2_schema_has_no_host_turn_id_and_binds_finalize(self):
        tools = CLIENT.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        start = next(tool for tool in tools if tool["name"] == "quarry_start")
        finalize = next(tool for tool in tools if tool["name"] == "quarry_finalize")
        self.assertNotIn("activation_turn_id", json.dumps(start))
        self.assertEqual(finalize["inputSchema"]["required"], ["run_id", "run_capability", "question"])

    def test_public_skill_requires_honest_mode_label(self):
        skill = (ROOT / "skills" / "quarry" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Full Quarry \u2022 run qr_...", skill)
        self.assertIn("Quarry Skill Only \u2022 hosted verification not run", skill)
        self.assertIn("Never invent a run ID", skill)
        self.assertIn("Never create, guess, copy, or send a host/chat turn identifier", skill)
        self.assertIn("privacy-preserving choice", skill)
        self.assertIn("rejected receipt, failed handshake, activation error, or hosted outage", skill)

    def test_missing_endpoint_fails_closed(self):
        with patch.dict(os.environ, {"QUARRY_CONFIG_FILE": "/definitely/missing/quarry.json"}, clear=True), \
             patch.object(CLIENT, "DEFAULT_API_URL", ""):
            result = CLIENT.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                    "params": {"name": "quarry_start", "arguments": {"question": "x"}}})
        self.assertTrue(result["result"]["isError"])
        self.assertIn("not configured", result["result"]["content"][0]["text"])

    def test_api_token_stays_in_header(self):
        captured = {}

        def fake_open(request, timeout=0):
            captured["url"] = request.full_url
            captured["authorization"] = request.headers.get("Authorization")
            captured["body"] = request.data
            return Response({"run_id": "qr_test", "next_tool": "quarry_submit"})

        with patch.dict(os.environ, {"QUARRY_API_URL": "https://api.example.test",
                                     "QUARRY_API_KEY": "test-token"}, clear=True), \
             patch.object(CLIENT.urllib.request, "urlopen", side_effect=fake_open):
            result = CLIENT.call_tool("quarry_start", {"question": "Map this market"})
        self.assertEqual(result["run_id"], "qr_test")
        self.assertEqual(captured["authorization"], "Bearer test-token")
        self.assertNotIn(b"test-token", captured["body"])

    def test_no_key_uses_persistent_private_client_identity(self):
        captured = []

        def fake_open(request, timeout=0):
            captured.append(request.headers.get("X-quarry-client-id"))
            return Response({"ok": True})

        with self.subTest("identity persists"), __import__("tempfile").TemporaryDirectory() as tmp:
            identity_file = str(Path(tmp) / "client_id")
            with patch.dict(os.environ, {"QUARRY_API_URL": "https://api.example.test",
                                         "QUARRY_API_KEY": "", "QUARRY_CLIENT_ID_FILE": identity_file}, clear=True), \
                 patch.object(CLIENT.urllib.request, "urlopen", side_effect=fake_open):
                CLIENT._call_api("/v2/research/start", {"question": "one"})
                CLIENT._call_api("/v2/research/start", {"question": "two"})
        self.assertEqual(captured[0], captured[1])
        self.assertTrue(captured[0].startswith("qc_"))

    def test_shared_config_supplies_endpoint(self):
        with __import__("tempfile").TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.json"
            config.write_text(json.dumps({"api_url": "https://regional.example.test"}))
            with patch.dict(os.environ, {"QUARRY_CONFIG_FILE": str(config)}, clear=True):
                base, token = CLIENT._config()
        self.assertEqual(base, "https://regional.example.test")
        self.assertEqual(token, "")

    def test_default_start_uses_v2_and_never_sends_turn_identifier(self):
        captured = {}

        def fake_open(request, timeout=0):
            captured["url"] = request.full_url
            captured["payload"] = json.loads(request.data)
            return Response({"run_id": "qr_test", "run_capability": "cap_test"})

        with patch.dict(os.environ, {"QUARRY_API_URL": "https://api.example.test",
                                     "QUARRY_API_KEY": "test-token"}, clear=True), \
             patch.object(CLIENT.urllib.request, "urlopen", side_effect=fake_open):
            CLIENT.call_tool("quarry_start", {"question": "Map this market"})
        self.assertEqual(captured["url"], "https://api.example.test/v2/research/start")
        self.assertEqual(captured["payload"]["question"], "Map this market")
        self.assertNotIn("activation_turn_id", captured["payload"])

    def test_explicit_v1_rollback_retains_legacy_tools(self):
        with patch.dict(os.environ, {"QUARRY_PROTOCOL": "v1"}, clear=False):
            tools = CLIENT.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools],
                         ["quarry_start", "quarry_submit", "quarry_finalize", "quarry_status"])

    def test_v2_lifecycle_relays_server_capability_and_canonical_question(self):
        calls = []

        def fake_call(path, payload=None, method="POST"):
            calls.append((path, payload, method))
            return {"ok": True}

        with patch.object(CLIENT, "_call_api", side_effect=fake_call):
            CLIENT.call_tool("quarry_submit", {
                "run_id": "qr_test", "run_capability": "cap_test",
                "question": "Canonical question", "candidates": [{"title": "A"}],
            })
            CLIENT.call_tool("quarry_finalize", {
                "run_id": "qr_test", "run_capability": "cap_test",
                "question": "Canonical question",
            })
            CLIENT.call_tool("quarry_artifact", {
                "artifact_id": "qa_test", "retrieval_token": "rt_test",
            })
            CLIENT.handshake()
        self.assertEqual([call[0] for call in calls], [
            "/v2/research/submit", "/v2/research/finalize",
            "/v2/research/artifact", "/v2/doctor",
        ])
        self.assertEqual(calls[0][1]["run_capability"], "cap_test")
        self.assertEqual(calls[0][1]["question"], "Canonical question")
        self.assertNotIn("activation_turn_id", json.dumps(calls))


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(not result.result.wasSuccessful())
