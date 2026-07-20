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


class Response:
    def __init__(self, payload: dict):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit=-1):
        return self.payload[:limit] if limit >= 0 else self.payload


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
        user_home = Path(temporary) / "user-home"
        home = user_home / "quarry-home"
        args = installer.parse_args(["--source-dir", str(ROOT)])
        with mock.patch.dict(os.environ, {"HOME": str(user_home), "QUARRY_HOME": str(home)}, clear=False), \
             mock.patch.object(installer, "_detected_agents", return_value=[]), \
             mock.patch.object(installer, "_service_health", return_value=(True, "reachable")):
            assert installer.install(args) == 1
        client = home / "client" / "quarry_mcp.py"
        skill = home / "skills" / "quarry" / "SKILL.md"
        assert client.is_file() and os.access(client, os.X_OK)
        assert skill.is_file()
        assert "quarry_start" in client.read_text()


def test_agent_selection() -> None:
    assert installer.SUPPORTED_AGENTS == ("claude", "codex", "gemini", "cursor", "vscode")
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


def test_protocol_handshake_lists_every_full_quarry_tool() -> None:
    assert installer._protocol_tools(ROOT / "client" / "quarry_mcp.py") == installer.EXPECTED_TOOLS
    assert installer.EXPECTED_TOOLS == (
        "quarry_start", "quarry_submit", "quarry_finalize", "quarry_artifact")


def test_service_doctor_uses_v2_contract() -> None:
    captured = {}

    def fake_open(request, timeout=0):
        captured["url"] = request.full_url
        captured["client_id"] = request.headers.get("X-quarry-client-id")
        return Response({"ready": True, "deployment_id": "deployment-test"})

    with tempfile.TemporaryDirectory() as temporary, \
         mock.patch.dict(os.environ, {"QUARRY_HOME": temporary,
                                      "QUARRY_CLIENT_ID": "client-test"}, clear=False), \
         mock.patch.object(installer.urllib.request, "urlopen", side_effect=fake_open):
        ready, detail = installer._service_health("https://api.example.test")
    assert ready is True
    assert captured["url"] == "https://api.example.test/v2/doctor"
    assert captured["client_id"] == "client-test"
    assert "deployment-test" in detail


def test_doctor_fails_when_agent_registration_is_missing() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        user_home = Path(temporary) / "user-home"
        quarry_home = user_home / ".quarry"
        client = quarry_home / "client" / "quarry_mcp.py"
        skill = user_home / ".agents" / "skills" / "quarry" / "SKILL.md"
        agent_skill = user_home / ".codex" / "skills" / "quarry" / "SKILL.md"
        client.parent.mkdir(parents=True)
        client.write_bytes((ROOT / "client" / "quarry_mcp.py").read_bytes())
        client.chmod(0o755)
        skill.parent.mkdir(parents=True)
        skill.write_bytes((ROOT / "skills" / "quarry" / "SKILL.md").read_bytes())
        agent_skill.parent.mkdir(parents=True)
        agent_skill.write_bytes(skill.read_bytes())
        args = installer.parse_args(["--doctor", "--agent", "codex"])
        with mock.patch.dict(os.environ, {"HOME": str(user_home), "QUARRY_HOME": str(quarry_home)}, clear=False), \
             mock.patch.object(installer, "_service_health", return_value=(True, "reachable")), \
             mock.patch.object(installer, "_detected_agents", return_value=["codex"]), \
             mock.patch.object(installer, "_registration_ready", return_value=(False, "registration missing")):
            assert installer.doctor(args) == 1


def test_doctor_passes_only_with_skill_tools_service_and_registration() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        user_home = Path(temporary) / "user-home"
        args = installer.parse_args(["--source-dir", str(ROOT), "--agent", "codex"])
        with mock.patch.dict(os.environ, {"HOME": str(user_home), "QUARRY_HOME": str(user_home / ".quarry")}, clear=False), \
             mock.patch.object(installer, "_detected_agents", return_value=["codex"]), \
             mock.patch.object(installer.shutil, "which", side_effect=lambda command: "/tmp/codex" if command == "codex" else None), \
             mock.patch.object(installer, "_register_cli"), \
             mock.patch.object(installer, "_service_health", return_value=(True, "reachable")), \
             mock.patch.object(installer, "_registration_ready", return_value=(True, "registered")):
            assert installer.install(args) == 0


def test_doctor_covers_every_supported_agent_host() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        user_home = Path(temporary) / "user-home"
        quarry_home = user_home / ".quarry"
        client = quarry_home / "client" / "quarry_mcp.py"
        skill_bytes = (ROOT / "skills" / "quarry" / "SKILL.md").read_bytes()
        client.parent.mkdir(parents=True)
        client.write_bytes((ROOT / "client" / "quarry_mcp.py").read_bytes())
        client.chmod(0o755)
        for path in (
            user_home / ".agents/skills/quarry/SKILL.md",
            user_home / ".claude/skills/quarry/SKILL.md",
            user_home / ".codex/skills/quarry/SKILL.md",
            user_home / ".gemini/skills/quarry/SKILL.md",
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(skill_bytes)
        args = installer.parse_args(["--doctor", "--agent", "all"])
        with mock.patch.dict(os.environ, {"HOME": str(user_home), "QUARRY_HOME": str(quarry_home)}, clear=False), \
             mock.patch.object(installer, "_service_health", return_value=(True, "reachable")), \
             mock.patch.object(installer, "_detected_agents", return_value=list(installer.SUPPORTED_AGENTS)), \
             mock.patch.object(installer, "_registration_ready", return_value=(True, "registered")):
            assert installer.doctor(args) == 0


def main() -> int:
    test_cursor_merge_preserves_existing()
    test_local_install_without_detected_agent()
    test_agent_selection()
    test_manual_config_contains_endpoint_and_client()
    test_cli_registration_uses_shared_client()
    test_protocol_handshake_lists_every_full_quarry_tool()
    test_service_doctor_uses_v2_contract()
    test_doctor_fails_when_agent_registration_is_missing()
    test_doctor_passes_only_with_skill_tools_service_and_registration()
    test_doctor_covers_every_supported_agent_host()
    print("Universal installer tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
