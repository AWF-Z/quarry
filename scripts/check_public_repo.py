#!/usr/bin/env python3
"""Offline validation for Quarry's public repository."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = (
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "install.py",
    ".github/CODEOWNERS",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".mcp.json",
    "client/quarry_mcp.py",
    "skills/quarry/SKILL.md",
    "scripts/test_universal_installer.py",
)
SECRET_PATTERNS = (
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
)
ABSOLUTE_PRIVATE_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def check_json(errors: list[str]) -> None:
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", ".mcp.json"):
        try:
            json.loads((ROOT / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(errors, f"{rel}: invalid JSON: {exc}")


def check_xml(errors: list[str]) -> None:
    for path in ROOT.glob("docs/assets/**/*.svg"):
        try:
            ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            fail(errors, f"{path.relative_to(ROOT)}: invalid SVG XML: {exc}")


def check_markdown_links(errors: list[str]) -> None:
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or target.startswith(("https://", "http://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                fail(errors, f"{path.relative_to(ROOT)}: broken link: {target}")


def check_front_matter(errors: list[str]) -> None:
    paths = list((ROOT / "commands").glob("*.md")) + [ROOT / "skills/quarry/SKILL.md"]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or text.find("\n---\n", 4) < 0:
            fail(errors, f"{path.relative_to(ROOT)}: missing YAML front matter")
        if "description:" not in text.split("\n---\n", 1)[0]:
            fail(errors, f"{path.relative_to(ROOT)}: front matter needs a description")


def check_release_hygiene(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            fail(errors, f"{path.relative_to(ROOT)}: symlinks are not allowed")
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if ABSOLUTE_PRIVATE_PATH.search(text):
            fail(errors, f"{path.relative_to(ROOT)}: contains an absolute user path")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(errors, f"{path.relative_to(ROOT)}: resembles a committed credential")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            fail(errors, f"missing required file: {rel}")
    check_json(errors)
    check_xml(errors)
    check_markdown_links(errors)
    check_front_matter(errors)
    check_release_hygiene(errors)

    if errors:
        print("Public repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Public repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
