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
                         ["quarry_start", "quarry_submit", "quarry_finalize", "quarry_status"])

    def test_missing_endpoint_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(CLIENT, "DEFAULT_API_URL", ""):
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
                CLIENT._call_api("/v1/research/start", {"question": "one"})
                CLIENT._call_api("/v1/research/start", {"question": "two"})
        self.assertEqual(captured[0], captured[1])
        self.assertTrue(captured[0].startswith("qc_"))


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    sys.exit(not result.result.wasSuccessful())
