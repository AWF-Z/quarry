#!/usr/bin/env python3
"""Universal installer for Quarry's public MCP client and Agent Skill."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


VERSION = "1.0.1"
DEFAULT_SOURCE_BASE = "https://raw.githubusercontent.com/AWF-Z/quarry/v1.0.1"
DEFAULT_API_URL = "https://quarry-core-awfz.fly.dev"
SUPPORTED_AGENTS = ("claude", "codex", "gemini", "cursor", "vscode")


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

    if not configured:
        print("\nNo supported agent CLI was detected. Quarry is installed; add this MCP configuration to your agent:")
        print(_manual_config(client_path, api_url))
    else:
        print("\nQuarry is ready in: " + ", ".join(configured))
        print("Restart open agent sessions, then research normally.")
    return 0


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
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    if not args.agent:
        args.agent = ["auto"]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return uninstall(args) if args.uninstall else install(args)
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"Quarry installation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
