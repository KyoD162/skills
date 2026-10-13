#!/usr/bin/env python3
"""Fail when the published skill drifts from the server's tool surface.

Reads the tool definitions from the second-brain MCP server's ``tools.py``
(either from ``TOOLS_SOURCE``, or over the GitHub API using
``SERVER_REPO_TOKEN``) and verifies that every tool is documented in the skill,
and that the skill documents no tool the server does not define.
"""

from __future__ import annotations

import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = "DeikuModder/second-brain-mcp-server"
TOOLS_PATH = "src/second_brain_mcp/tools.py"
SKILL_DIR = Path("plugins/taste-second-brain/skills/taste-second-brain")
SKILL = SKILL_DIR / "SKILL.md"
REFS = SKILL_DIR / "references/tools.md"

TOOL_DEF_RE = re.compile(r"@server\.tool\([\s\S]*?async def (\w+)\(")
TABLE_ROW_RE = re.compile(r"^\|\s*`(\w+)`\s*\|", re.M)


def fetch_tools_source() -> str:
    local = os.environ.get("TOOLS_SOURCE")
    if local:
        return Path(local).read_text(encoding="utf-8")
    token = os.environ.get("SERVER_REPO_TOKEN")
    if not token:
        sys.exit(
            "::error::SERVER_REPO_TOKEN is not set. Add a fine-grained PAT with "
            f"read-only Contents access to {REPO} as a repository secret."
        )
    url = f"https://api.github.com/repos/{REPO}/contents/{TOOLS_PATH}?ref=main"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.raw+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "skill-drift-check",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        sys.exit(f"::error::Could not fetch {TOOLS_PATH} from {REPO}: {exc}")


def main() -> int:
    tools = set(TOOL_DEF_RE.findall(fetch_tools_source()))
    if not tools:
        print("::error::No tools extracted from tools.py — the extraction regex may be stale")
        return 1

    skill = SKILL.read_text(encoding="utf-8")
    refs = REFS.read_text(encoding="utf-8")
    documented = set(TABLE_ROW_RE.findall(skill))

    errors: list[str] = []
    for name in sorted(tools):
        if f"`{name}`" not in skill:
            errors.append(f"tool `{name}` is defined in tools.py but not mentioned in SKILL.md")
        if f"`{name}`" not in refs:
            errors.append(f"tool `{name}` is defined in tools.py but not mentioned in references/tools.md")
    for name in sorted(documented - tools):
        errors.append(f"SKILL.md documents `{name}`, but tools.py does not define it")

    print(f"tools.py defines {len(tools)}: {sorted(tools)}")
    print(f"SKILL.md table lists {len(documented)}: {sorted(documented)}")
    if errors:
        for message in errors:
            print(f"::error::{message}")
        return 1
    print("OK: published skill matches the server tool surface")
    return 0


if __name__ == "__main__":
    sys.exit(main())
