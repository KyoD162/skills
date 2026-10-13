# Taste Network skills hub

Importable agent skills for Taste Network. This repository is a distribution
hub: it holds skills only — no servers, no credentials, no MCP tokens.

## Contents

- `taste-second-brain/SKILL.md` — how to use the Taste Network "second brain"
  MCP server: progressive, tier-respecting retrieval and conservative writes.
- `taste-second-brain/references/tools.md` — exact tool schemas and response
  shapes.

The skill is an instruction layer. It is **not** authentication, a permission
system, or a substitute for server-side authorization. Access to the brain comes
from the MCP connection and the bearer token, both configured separately.

## Canonical source

The canonical copy of `taste-second-brain/` lives in the server repository
(`second-brain-mcp-server/skills/`) so it changes together with the tools it
documents. This hub mirrors it. Do not edit skills here independently — update
the server repo, then re-publish here.

## Import per platform

- **Claude** (claude.ai, desktop, Cowork) — Customize → Skills → add/upload the
  skill. Uses only the Agent Skills spec frontmatter (`name`, `description`).
- **Claude Code** — place at `.claude/skills/taste-second-brain/SKILL.md`, or
  install as a plugin.
- **ChatGPT** — Plugins → Skills → Create → *Upload from your computer* (or a
  workspace admin uploads it). Personal Skills require a qualifying
  Business/Enterprise/Healthcare/Edu workspace.
- **Manus** — Skills tab → *+ Add* → **Import from GitHub** (this repo) or
  *Upload a skill* (`.zip` / `.skill` / folder). Invoke with `/`.
- **opencode** — `.opencode/skills/<name>/SKILL.md`, or point `skills.paths` in
  `opencode.json` at a checkout of this repo.

## Security boundary

- Every retrieval and write is authorized server-side from the caller's token.
  A denial is final.
- Client isolation is **not** implemented; do not claim per-client isolation.
- Never commit MCP tokens, connector configs, or other credentials to this repo.
