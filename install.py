#!/usr/bin/env python3
"""Universal installer for Quarry's public MCP client and Agent Skill."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


VERSION = "1.0.3"
DEFAULT_SOURCE_BASE = "https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.3"
DEFAULT_API_URL = "https://quarry-core-awfz.fly.dev"
SUPPORTED_AGENTS = ("claude", "codex", "gemini", "cursor", "vscode")
EXPECTED_TOOLS = ("quarry_start", "quarry_submit", "quarry_finalize", "quarry_artifact")


def _home() -> Path:
    return Path(os.environ.get("QUARRY_HOME", "~/.quarry")).expanduser()


def _read_asset(relative: str, args: argparse.Namespace) -> bytes:
    if args.source_dir:
        return (Path(args.source_dir).expanduser() / relative).read_bytes()
    base = (args.source_base or os.environ.get("QUARRY_DISTRIBUTION_URL") or DEFAULT_SOURCE_BASE).rstrip("/")
    request = urllib.request.Request(
        f"{base}/{relative}",
        headers={"User-Agent": f"Quarry-Installer/{VERSION}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(2_000_001)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Could not download Quarry. Set QUARRY_DISTRIBUTION_URL to a reachable mirror "
            "or use --source-dir with a local checkout."
        ) from exc


def _atomic_write(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.chmod(mode)
    temporary.replace(path)


def _run(command: list[str], *, check: bool = True, quiet: bool = False) -> subprocess.CompletedProcess:
    if not quiet:
        print("  $ " + " ".join(command))
    return subprocess.run(command, check=check, text=True, capture_output=quiet)


def _protocol_tools(client: Path) -> tuple[str, ...]:
    requests = (
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "doctor"}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    payload = "".join(json.dumps(item, separators=(",", ":")) + "\n" for item in requests)
    environment = dict(os.environ)
    environment.pop("QUARRY_PROTOCOL", None)
    completed = subprocess.run(
        [sys.executable or "python3", str(client)], input=payload, text=True,
        capture_output=True, timeout=10, check=False, env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError("the Quarry MCP client did not start")
    responses = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    if len(responses) != 2 or responses[0].get("result", {}).get("serverInfo", {}).get("name") != "quarry-core":
        raise RuntimeError("the Quarry MCP handshake was invalid")
    tools = responses[1].get("result", {}).get("tools", [])
    return tuple(tool.get("name", "") for tool in tools)


def _detected_agents() -> list[str]:
    detected = []
    commands = {
        "claude": "claude",
        "codex": "codex",
        "gemini": "gemini",
        "cursor": "cursor-agent",
        "vscode": "code",
    }
    for agent, command in commands.items():
        if shutil.which(command):
            detected.append(agent)
    return detected


def _install_skill(agent: str, skill: bytes) -> None:
    paths = {
        "claude": Path("~/.claude/skills/quarry/SKILL.md").expanduser(),
        "codex": Path("~/.codex/skills/quarry/SKILL.md").expanduser(),
        "gemini": Path("~/.gemini/skills/quarry/SKILL.md").expanduser(),
    }
    if agent in paths:
        _atomic_write(paths[agent], skill)


def _register_cli(agent: str, client: Path) -> None:
    python = sys.executable or "python3"
    if agent == "claude":
        _run(["claude", "mcp", "remove", "-s", "user", "quarry"], check=False, quiet=True)
        _run(["claude", "mcp", "add", "-s", "user", "quarry", "--", python, str(client)])
    elif agent == "codex":
        _run(["codex", "mcp", "remove", "quarry"], check=False, quiet=True)
        _run(["codex", "mcp", "add", "quarry", "--", python, str(client)])
    elif agent == "gemini":
        _run(["gemini", "mcp", "remove", "-s", "user", "quarry"], check=False, quiet=True)
        _run(["gemini", "mcp", "add", "-s", "user", "quarry", python, str(client)])


def _merge_cursor_config(client: Path, api_url: str) -> None:
    path = Path("~/.cursor/mcp.json").expanduser()
    data = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError(f"Cursor configuration is not a JSON object: {path}")
    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise RuntimeError(f"Cursor mcpServers is not a JSON object: {path}")
    servers["quarry"] = {
        "command": sys.executable or "python3",
        "args": [str(client)],
        "env": {"QUARRY_API_URL": api_url},
    }
    _atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())


def _register_vscode(client: Path, api_url: str) -> None:
    definition = json.dumps({
        "name": "quarry",
        "command": sys.executable or "python3",
        "args": [str(client)],
        "env": {"QUARRY_API_URL": api_url},
    }, separators=(",", ":"))
    _run(["code", "--add-mcp", definition])


def _manual_config(client: Path, api_url: str) -> str:
    return json.dumps({
        "mcpServers": {
            "quarry": {
                "command": sys.executable or "python3",
                "args": [str(client)],
                "env": {"QUARRY_API_URL": api_url},
            }
        }
    }, ensure_ascii=False, indent=2)


def _config_has_quarry(path: Path, client: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        definition = data.get("mcpServers", {}).get("quarry", {})
        return str(client) in [str(value) for value in definition.get("args", [])]
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def _registration_ready(agent: str, client: Path) -> tuple[bool, str]:
    if agent == "claude":
        if not shutil.which("claude"):
            return False, "Claude Code CLI is not installed"
        result = _run(["claude", "mcp", "get", "quarry"], check=False, quiet=True)
        return result.returncode == 0, "registered" if result.returncode == 0 else "registration missing"
    if agent == "codex":
        if not shutil.which("codex"):
            return False, "Codex CLI is not installed"
        result = _run(["codex", "mcp", "get", "quarry"], check=False, quiet=True)
        return result.returncode == 0, "registered" if result.returncode == 0 else "registration missing"
    if agent == "gemini":
        if not shutil.which("gemini"):
            return False, "Gemini CLI is not installed"
        result = _run(["gemini", "mcp", "list"], check=False, quiet=True)
        output = (result.stdout or "") + (result.stderr or "")
        ready = result.returncode == 0 and "quarry" in output.casefold()
        return ready, "registered" if ready else "registration missing"
    if agent == "cursor":
        ready = _config_has_quarry(Path("~/.cursor/mcp.json").expanduser(), client)
        return ready, "registered" if ready else "registration missing"
    if agent == "vscode":
        state_path = _home() / "install-state.json"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            ready = "vscode" in state.get("configured_agents", []) and client.is_file()
        except (OSError, ValueError, TypeError):
            ready = False
        return ready, "registration accepted by VS Code" if ready else "registration not confirmed"
    return False, "unsupported agent"


def _agent_skill_ready(agent: str) -> bool:
    destinations = {
        "claude": Path("~/.claude/skills/quarry/SKILL.md").expanduser(),
        "codex": Path("~/.codex/skills/quarry/SKILL.md").expanduser(),
        "gemini": Path("~/.gemini/skills/quarry/SKILL.md").expanduser(),
    }
    path = destinations.get(agent, Path("~/.agents/skills/quarry/SKILL.md").expanduser())
    try:
        return path.is_file() and "name: quarry" in path.read_text(encoding="utf-8")
    except OSError:
        return False


def _service_health(api_url: str) -> tuple[bool, str]:
    headers = {"User-Agent": f"Quarry-Doctor/{VERSION}"}
    token = os.environ.get("QUARRY_API_KEY", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        identity_path = Path(os.environ.get("QUARRY_CLIENT_ID_FILE", _home() / "client_id")).expanduser()
        identity = os.environ.get("QUARRY_CLIENT_ID", "").strip()
        if not identity:
            try:
                identity = identity_path.read_text().strip()
            except OSError:
                identity = ""
        if not identity:
            identity = "qc_" + secrets.token_urlsafe(24)
            _atomic_write(identity_path, (identity + "\n").encode(), 0o600)
        headers["X-Quarry-Client-ID"] = identity
    request = urllib.request.Request(api_url.rstrip("/") + "/v2/doctor",
                                     headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read(64_000))
        ready = bool(payload.get("ready"))
        detail = f"protocol v2 ready ({payload.get('deployment_id', 'deployment unknown')})"
        return ready, detail if ready else "protocol v2 doctor returned not-ready"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return False, f"unreachable ({type(exc).__name__})"


def doctor(args: argparse.Namespace, *, agents: list[str] | None = None) -> int:
    root = _home()
    client = root / "client" / "quarry_mcp.py"
    shared_skill = Path("~/.agents/skills/quarry/SKILL.md").expanduser()
    api_url = (args.api_url or os.environ.get("QUARRY_API_URL") or DEFAULT_API_URL).rstrip("/")
    selected = agents if agents is not None else _select_agents(args.agent)
    failures = []

    print("\nQuarry doctor")
    client_ready = client.is_file() and os.access(client, os.X_OK)
    print(f"- shared MCP client: {'ready' if client_ready else 'missing'}")
    if not client_ready:
        failures.append("shared MCP client")
    skill_ready = shared_skill.is_file() and "name: quarry" in shared_skill.read_text(encoding="utf-8")
    print(f"- shared Quarry skill: {'ready' if skill_ready else 'missing'}")
    if not skill_ready:
        failures.append("shared Quarry skill")

    try:
        tools = _protocol_tools(client) if client_ready else ()
        protocol_ready = tools == EXPECTED_TOOLS
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
        protocol_ready = False
        tools = ()
    print(f"- MCP tool handshake: {'ready' if protocol_ready else 'failed'}"
          + (f" ({', '.join(tools)})" if tools else ""))
    if not protocol_ready:
        failures.append("MCP tool handshake")

    health_ready, health_detail = _service_health(api_url)
    print(f"- hosted engine: {health_detail}")
    if not health_ready:
        failures.append("hosted engine")

    checked = []
    for agent in selected:
        if agent not in SUPPORTED_AGENTS:
            continue
        installed = agent in _detected_agents() or agent == "cursor"
        if not installed and agents is None:
            print(f"- {agent}: not installed, skipped")
            continue
        ready, detail = _registration_ready(agent, client)
        agent_skill_ready = _agent_skill_ready(agent)
        print(f"- {agent}: skill {'ready' if agent_skill_ready else 'missing'}; MCP {detail}")
        checked.append(agent)
        if not ready:
            failures.append(f"{agent} registration")
        if not agent_skill_ready:
            failures.append(f"{agent} skill")

    if not checked:
        print("- agent registration: none configured")
        failures.append("agent registration")
    if failures:
        print("Doctor result: INCOMPLETE. Run the installer again, then restart the affected agent.")
        return 1
    print("Doctor result: QUARRY INSTALLATION READY. Restart open agent sessions once after installation.")
    return 0


def _select_agents(requested: list[str]) -> list[str]:
    if "all" in requested:
        return list(SUPPORTED_AGENTS)
    if "auto" in requested:
        return _detected_agents()
    return list(dict.fromkeys(requested))


def install(args: argparse.Namespace) -> int:
    agents = _select_agents(args.agent)
    root = _home()
    client_path = root / "client" / "quarry_mcp.py"
    skill_path = root / "skills" / "quarry" / "SKILL.md"
    api_url = (args.api_url or os.environ.get("QUARRY_API_URL") or DEFAULT_API_URL).rstrip("/")

    print("Installing Quarry")
    client = _read_asset("client/quarry_mcp.py", args)
    skill = _read_asset("skills/quarry/SKILL.md", args)
    _atomic_write(client_path, client, 0o755)
    _atomic_write(skill_path, skill)
    _atomic_write(root / "config.json", (json.dumps({"api_url": api_url}, indent=2) + "\n").encode(), 0o600)
    _atomic_write(Path("~/.agents/skills/quarry/SKILL.md").expanduser(), skill)

    configured = []
    for agent in agents:
        if agent not in SUPPORTED_AGENTS:
            raise RuntimeError(f"Unsupported agent: {agent}")
        if agent in ("claude", "codex", "gemini"):
            command = agent
            if not shutil.which(command):
                print(f"- {agent}: not installed, skipped")
                continue
            _register_cli(agent, client_path)
            _install_skill(agent, skill)
        elif agent == "cursor":
            _merge_cursor_config(client_path, api_url)
        elif agent == "vscode":
            if not shutil.which("code"):
                print("- vscode: code CLI not installed, skipped")
                continue
            _register_vscode(client_path, api_url)
        configured.append(agent)
        print(f"- {agent}: ready")

    _atomic_write(root / "install-state.json", (json.dumps({
        "version": VERSION,
        "protocol_version": "2",
        "configured_agents": configured,
        "restart_required": bool(configured),
    }, indent=2) + "\n").encode(), 0o600)

    if not configured:
        print("\nNo supported agent CLI was detected. Quarry is installed; add this MCP configuration to your agent:")
        print(_manual_config(client_path, api_url))
    else:
        print("\nQuarry is ready in: " + ", ".join(configured))
        print("Restart open agent sessions once, then research normally.")
    return doctor(args, agents=configured)


def uninstall(args: argparse.Namespace) -> int:
    agents = _select_agents(args.agent)
    for agent in agents:
        if agent == "claude" and shutil.which("claude"):
            _run(["claude", "mcp", "remove", "-s", "user", "quarry"], check=False)
        elif agent == "codex" and shutil.which("codex"):
            _run(["codex", "mcp", "remove", "quarry"], check=False)
        elif agent == "gemini" and shutil.which("gemini"):
            _run(["gemini", "mcp", "remove", "-s", "user", "quarry"], check=False)
    shutil.rmtree(_home(), ignore_errors=True)
    print("Removed Quarry's shared runtime. Cursor and VS Code entries can be removed from their MCP settings.")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Quarry for major AI coding agents.")
    parser.add_argument("--agent", action="append", choices=("auto", "all", *SUPPORTED_AGENTS), default=[])
    parser.add_argument("--api-url", help="Alternate Quarry service endpoint.")
    parser.add_argument("--source-base", help="Alternate public distribution mirror.")
    parser.add_argument("--source-dir", help="Install assets from a local Quarry checkout.")
    parser.add_argument("--doctor", action="store_true", help="Verify the skill, MCP client, service, and agent registrations.")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    if not args.agent:
        args.agent = ["auto"]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.doctor:
            return doctor(args)
        return uninstall(args) if args.uninstall else install(args)
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"Quarry installation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
