# Taste Network skills hub

Importable agent skills for Taste Network. This repository is a distribution
hub: it holds skills only — no servers, no credentials, no MCP tokens.

## Contents

```text
.claude-plugin/marketplace.json              # Claude plugin marketplace
.agents/plugins/marketplace.json             # Codex / ChatGPT marketplace catalog
plugins/taste-second-brain/
  .claude-plugin/plugin.json                 # Claude plugin manifest
  .codex-plugin/plugin.json                  # Codex plugin manifest
  skills/taste-second-brain/
    SKILL.md                                 # the skill
    references/tools.md                      # exact tool schemas
README.md
```

The skill is an instruction layer. It is **not** authentication, a permission
system, or a substitute for server-side authorization. Access to the brain comes
from the MCP connection and the bearer token, both configured separately.

## Canonical source

The canonical copy of the skill lives in the server repository
(`second-brain-mcp-server/skills/`) so it changes together with the tools it
documents. This hub mirrors it. Do not edit the skill here independently —
update the server repo, then re-publish this `skills/taste-second-brain/` tree
to `plugins/taste-second-brain/skills/taste-second-brain/`.

## Install per platform

### Claude (marketplace, auto-updating)

Claude Code / Claude Desktop:

```text
/plugin marketplace add KyoD162/skills
/plugin install taste-second-brain@taste-network-skills
```

claude.ai / Cowork: Customize → Plugins → add the marketplace `KyoD162/skills`,
then install `taste-second-brain`. The skill uses only the Agent Skills spec
frontmatter (`name`, `description`).

### Codex / ChatGPT (workspace marketplace, daily sync)

A workspace admin imports this repository as a plugin marketplace (catalog at
`.agents/plugins/marketplace.json`) and keeps it up to date with daily sync.
The admin can set the installation policy so `taste-second-brain` installs for
the workspace. Skills require a qualifying Business/Enterprise/Healthcare/Edu
workspace.

Without a workspace, the skill can also be uploaded directly:
Plugins → Skills → *Create → Upload from your computer* (the
`plugins/taste-second-brain/skills/` folder).

### Manus

Skills tab → *+ Add* → **Import from GitHub** (repo `KyoD162/skills`) or
*Upload a skill* (`.zip` / `.skill` / folder). Invoke with `/`.
*(Assumption: Manus scans the repository for `SKILL.md`; exact layout not
documented.)*

### opencode

Point `skills.paths` at a checkout, or copy
`plugins/taste-second-brain/skills/taste-second-brain/` into
`.opencode/skills/taste-second-brain/`.

## Drift check (CI)

`.github/workflows/skill-drift.yml` runs weekly (and on demand). It reads
`src/second_brain_mcp/tools.py` from `DeikuModder/second-brain-mcp-server` and
fails if a tool was added, renamed, or removed without a matching update here
(in `SKILL.md` and `references/tools.md`).

It fetches that file over the GitHub API, so the repository needs one secret:

- `SERVER_REPO_TOKEN` — a fine-grained PAT with **read-only Contents** access
  to `DeikuModder/second-brain-mcp-server`. Add it under
  Settings → Secrets and variables → Actions. Until it exists, the job fails
  with a clear message.

Run it locally without the secret:

```bash
TOOLS_SOURCE=/path/to/tools.py python scripts/check_skill_drift.py
```

## Security boundary

- Every retrieval and write is authorized server-side from the caller's token.
  A denial is final.
- Client isolation is **not** implemented; do not claim per-client isolation.
- Never commit MCP tokens, connector configs, or other credentials to this repo.
