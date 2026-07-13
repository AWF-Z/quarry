#!/usr/bin/env python3
"""Offline tests for Quarry's universal installer."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("quarry_install", ROOT / "install.py")
installer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(installer)


def test_cursor_merge_preserves_existing() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        config = home / ".cursor" / "mcp.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"mcpServers": {"existing": {"command": "keep"}}, "setting": True}))
        with mock.patch.dict(os.environ, {"HOME": str(home)}, clear=False):
            installer._merge_cursor_config(home / "client.py", "https://example.test")
        result = json.loads(config.read_text())
        assert result["setting"] is True
        assert result["mcpServers"]["existing"]["command"] == "keep"
        assert result["mcpServers"]["quarry"]["env"]["QUARRY_API_URL"] == "https://example.test"


def test_local_install_without_detected_agent() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary) / "quarry-home"
        args = installer.parse_args(["--source-dir", str(ROOT)])
        with mock.patch.dict(os.environ, {"QUARRY_HOME": str(home)}, clear=False), \
             mock.patch.object(installer, "_detected_agents", return_value=[]):
            assert installer.install(args) == 0
        client = home / "client" / "quarry_mcp.py"
        skill = home / "skills" / "quarry" / "SKILL.md"
        assert client.is_file() and os.access(client, os.X_OK)
        assert skill.is_file()
        assert "quarry_start" in client.read_text()


def test_agent_selection() -> None:
    with mock.patch.object(installer, "_detected_agents", return_value=["codex", "cursor"]):
        assert installer._select_agents(["auto"]) == ["codex", "cursor"]
    assert installer._select_agents(["codex", "codex", "gemini"]) == ["codex", "gemini"]
    assert installer._select_agents(["all"]) == list(installer.SUPPORTED_AGENTS)


def test_manual_config_contains_endpoint_and_client() -> None:
    result = json.loads(installer._manual_config(Path("/tmp/quarry.py"), "https://example.test"))
    quarry = result["mcpServers"]["quarry"]
    assert quarry["args"] == ["/tmp/quarry.py"]
    assert quarry["env"]["QUARRY_API_URL"] == "https://example.test"


def test_cli_registration_uses_shared_client() -> None:
    with mock.patch.object(installer, "_run") as run:
        installer._register_cli("codex", Path("/tmp/quarry.py"))
    command = run.call_args_list[-1].args[0]
    assert command[:3] == ["codex", "mcp", "add"]
    assert command[-2:] == [installer.sys.executable, "/tmp/quarry.py"]


def main() -> int:
    test_cursor_merge_preserves_existing()
    test_local_install_without_detected_agent()
    test_agent_selection()
    test_manual_config_contains_endpoint_and_client()
    test_cli_registration_uses_shared_client()
    print("Universal installer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
