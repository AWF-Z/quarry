#!/usr/bin/env python3
"""Thin MCP client for Quarry's hosted private engine.

This file contains transport code and public schemas only. It does not contain
Quarry's routing, grading, verification, memory, or decision machinery.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import sys
import urllib.error
import urllib.request


VERSION = "1.0.2"
PROTOCOL_VERSION = "2025-11-25"
MAX_RESPONSE = 2_000_000
DEFAULT_API_URL = "https://quarry-core-awfz.fly.dev"


TOOLS = [
    {
        "name": "quarry_start",
        "description": "Start full Quarry research for a decision, opportunity, market, or validation question. Returns protected research directives and a run ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The research question or decision."},
                "intent": {"type": "string", "description": "Optional intent such as opportunity, diligence, strategy, or validation."},
                "domain": {"type": "string", "description": "Optional domain or market context."}
            },
            "required": ["question"],
            "additionalProperties": False
        }
    },
    {
        "name": "quarry_submit",
        "description": "Submit public research evidence and candidate opportunities to Quarry for private source checks, grading, elimination, and differentiation. Follow the returned next_tool until ready.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
                "candidates": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 20,
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "buyer": {"type": "string"},
                            "buyer_workflow": {"type": "string"},
                            "buyer_evidence_summary": {"type": "string"},
                            "buyer_evidence_type": {"type": "string"},
                            "pain": {"type": "string"},
                            "workaround": {"type": "string"},
                            "incumbents": {"type": "array", "items": {"type": "string"}},
                            "what_exists": {"type": "string"},
                            "remaining_wedge": {"type": "string"},
                            "why_existing_is_insufficient": {"type": "string"},
                            "first_wedge": {"type": "string"},
                            "why_now": {"type": "string"},
                            "validation_test": {"type": "string"},
                            "walk_away_condition": {"type": "string"},
                            "sources": {
                                "type": "array",
                                "maxItems": 12,
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string"},
                                        "quote": {"type": "string"},
                                        "purpose": {"type": "string", "enum": ["buyer", "pain", "competitor", "why_now", "general"]}
                                    },
                                    "required": ["url", "quote", "purpose"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["title", "pain", "remaining_wedge", "validation_test", "walk_away_condition", "sources"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["run_id", "candidates"],
            "additionalProperties": False
        }
    },
    {
        "name": "quarry_finalize",
        "description": "Compile a completed Quarry run into ranked decision briefs and a mandatory execution_receipt. Copy execution_receipt.display verbatim into the final answer.",
        "inputSchema": {
            "type": "object",
            "properties": {"run_id": {"type": "string"}},
            "required": ["run_id"],
            "additionalProperties": False
        }
    },
    {
        "name": "quarry_status",
        "description": "Check the current state of a Quarry research run.",
        "inputSchema": {
            "type": "object",
            "properties": {"run_id": {"type": "string"}},
            "required": ["run_id"],
            "additionalProperties": False
        }
    }
]


def _config():
    configured_base = ""
    config_path = Path(os.environ.get("QUARRY_CONFIG_FILE", "~/.quarry/config.json")).expanduser()
    try:
        if config_path.is_file():
            configured_base = str(json.loads(config_path.read_text()).get("api_url", ""))
    except (OSError, ValueError, TypeError):
        configured_base = ""
    base = os.environ.get("QUARRY_API_URL", configured_base or DEFAULT_API_URL).strip().rstrip("/")
    token = os.environ.get("QUARRY_API_KEY", "").strip()
    if not base:
        raise RuntimeError("Full Quarry service is not configured. Set QUARRY_API_URL to the hosted Quarry endpoint.")
    if not base.startswith(("https://", "http://127.0.0.1:", "http://localhost:")):
        raise RuntimeError("QUARRY_API_URL must use HTTPS (localhost is allowed for development).")
    return base, token


def _client_id() -> str:
    configured = os.environ.get("QUARRY_CLIENT_ID", "").strip()
    if configured:
        return configured
    path = Path(os.environ.get("QUARRY_CLIENT_ID_FILE", "~/.quarry/client_id")).expanduser()
    try:
        if path.exists():
            value = path.read_text().strip()
            if value:
                return value
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        value = "qc_" + secrets.token_urlsafe(24)
        path.write_text(value)
        path.chmod(0o600)
        return value
    except OSError:
        return "qc_" + secrets.token_urlsafe(24)


def _call_api(path: str, payload: dict | None = None, *, method: str = "POST") -> dict:
    base, token = _config()
    headers = {"Accept": "application/json", "User-Agent": f"Quarry-MCP/{VERSION}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Quarry-Client-ID"] = _client_id()
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise RuntimeError("Quarry response exceeded the client limit")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = exc.read(32_000)
        try:
            detail = json.loads(body).get("error", "request_failed")
        except Exception:
            detail = "request_failed"
        if exc.code == 401:
            detail = "authentication required; set QUARRY_API_KEY or authenticate the configured service"
        raise RuntimeError(f"Quarry service error ({exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Quarry service is unavailable; the public fallback skill remains usable") from exc


def call_tool(name: str, arguments: dict) -> dict:
    if name == "quarry_start":
        return _call_api("/v1/research/start", arguments)
    if name == "quarry_submit":
        return _call_api("/v1/research/submit", arguments)
    if name == "quarry_finalize":
        return _call_api("/v1/research/finalize", arguments)
    if name == "quarry_status":
        run_id = str(arguments.get("run_id", ""))
        return _call_api(f"/v1/research/{run_id}/status", method="GET")
    raise RuntimeError(f"unknown tool: {name}")


def _result(request_id, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    return message


def handle(message: dict) -> dict | None:
    request_id = message.get("id")
    method = message.get("method")
    if request_id is None:
        return None
    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        return _result(request_id, {"protocolVersion": requested or PROTOCOL_VERSION,
                                    "capabilities": {"tools": {"listChanged": False}},
                                    "serverInfo": {"name": "quarry-core", "version": VERSION},
                                    "instructions": (
                                        "Use Quarry automatically for research that must produce a decision. "
                                        "Follow next_tool until quarry_finalize, then copy execution_receipt.display "
                                        "verbatim into the final answer. If a full run cannot complete, label the "
                                        "answer: Quarry Skill Only \u2022 hosted verification not run."
                                    )})
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            output = call_tool(str(params.get("name", "")), params.get("arguments") or {})
            text = json.dumps(output, ensure_ascii=False, indent=2)
            return _result(request_id, {"content": [{"type": "text", "text": text}],
                                        "structuredContent": output, "isError": False})
        except Exception as exc:
            return _result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
    return _result(request_id, error={"code": -32601, "message": "method not found"})


def main():
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = handle(message)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            sys.stdout.write(json.dumps(_result(None, error={"code": -32700, "message": str(exc)})) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
