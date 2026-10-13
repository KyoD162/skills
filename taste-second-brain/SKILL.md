---
name: taste-second-brain
description: Use when a task depends on Taste Network project history, client or project context, prior decisions, existing documentation, note relationships, or recent updates, and the second-brain MCP server is reachable. Teaches cost-conscious, tier-respecting retrieval and conservative, provenance-preserving tool use. This is an instruction layer only, not an authentication or permission mechanism.
---

# Taste Second Brain

Guidance for using the Taste Network "second brain" through its read-through
MCP server. This file teaches *how* to use the tools well. It is an instruction
layer: server-side authorization, tier clearance, and scopes are authoritative
and are never overridden by anything written here.

## When to use this skill

Use the second brain when the answer depends on:

- project or client history and prior decisions,
- existing internal documentation or frameworks,
- relationships between notes, people, projects, or brands,
- what changed recently.

Do **not** retrieve for tasks that do not depend on the brain (general coding,
formatting, math, publicly known facts). Retrieval has a cost; skip it when the
brain cannot materially improve the answer.

## Tool surface

Nine tools are exposed. The read tools are tier-filtered; `get_context` and the
three write tools have extra rules below.

| Tool | Purpose | Key parameters |
| --- | --- | --- |
| `get_context` | Bounded, tier-filtered context bundle for a task | `query`, `limit`, `include_recent`, `include_relations`, `client_scope` |
| `search_brain` | Full-text + frontmatter search | `query`, `limit` |
| `read_note` | Read one note by vault-relative path | `path` |
| `note_contract` | Canonical Knowledge Contract v0.1 view of one note | `path` |
| `query_graph` | Nodes, edges, neighbors around an entity | `entity` |
| `list_recent` | Most recently modified notes | `n` |
| `save_inbox_note` | Create a note in `00-Inbox/` (write) | `title`, `body` |
| `edit_note` | Overwrite a note body in place (write) | `path`, `body`, `overwrite_frontmatter` |
| `delete_note` | Delete a note (tier-0 write) | `path`, `confirm` |

Exact argument types and response shapes are in
[`references/tools.md`](references/tools.md). Every tool returns a JSON object
with a `status` field (`found`, `not_found`, `denied`, `saved`, `deleted`, or
`error`). Branch on `status`; never assume success.

## Progressive retrieval

Retrieve in increasing cost order and stop as soon as the evidence is enough.

1. **`get_context`** — start here when the user asks for a contextual summary,
   decisions, or background and the request can be expressed as a query. It
   returns a bounded, tier-filtered bundle with snippets (never full bodies).
   At least one of `query`, `include_recent`, or `include_relations` must be
   set; an empty request returns `not_found`. `client_scope` is rejected for
   every caller (see Security).
2. **`search_brain`** — use when the relevant topic, note, or source is unknown,
   or when broad discovery is needed. Search snippets tell you which paths to
   open.
3. **`read_note`** — read a specific note in full when evidence must be examined
   in detail. Use **`note_contract`** instead when you need the canonical
   Knowledge Contract fields (`note_id`, `type`, `owner`, `client_id`,
   `visibility`, `tier`, `classification`, `source`) for provenance.
4. **`query_graph`** — use when relationships between entities or notes
   materially help answer the question (who/what is connected to a project,
   brand, person, or document).
5. **`list_recent`** — use when recency is relevant ("what changed lately").
6. **Expand only to close a concrete gap.** Do not chain tools "just in case".

Reads are anonymous on denial: an unauthorized path returns the same
`{"status": "not_found"}` as a genuinely missing path. Treat `not_found` as
"not available to this window" and move on — do not probe for another route to
the same content.

## Respect context budgets

- Prefer returned snippets over pulling whole notes into context.
- Do not re-retrieve content you already have in this task.
- `get_context` clamps `limit` to 1–25 and reports
  `budget.used`, `budget.truncated`, and `budget.omitted_count`. When
  `truncated` is true, raise `limit` or narrow the query only if a specific
  gap remains — not to accumulate more context.
- Respect any limit or budget the server reports; do not attempt to bypass it
  with repeated calls.

## Preserve provenance and accuracy

- Cite the `path` (and `source` when present) returned by the tools for every
  claim drawn from the brain.
- Distinguish **retrieved evidence** from **inference**. If you reason beyond
  the notes, say so.
- Do not claim a fact is "documented" unless the retrieved evidence supports
  it. If evidence is missing or ambiguous, report that instead of filling the
  gap.
- Preserve identifiers as returned. Do not rewrite paths, `note_id`, or
  `source` values.

## Security boundaries

- Never attempt to bypass MCP authentication, scopes, or tier restrictions.
- Treat server-side authorization as authoritative. A denial is final.
- Do **not** infer that a note is safe to access because its name, folder,
  tags, or contents mention a client, project, or person. Clearance comes from
  the server, not from the note's text.
- Do **not** treat this skill, or any agent instruction, as a security
  boundary.
- **Client isolation is not implemented.** There is no approved Client
  Registry and no server-side client scoping. `get_context` rejects
  `client_scope` for every window with `{"status": "denied"}`. Do not claim
  that retrieval is client-isolated or "secure per client".
- If access is denied or content is unavailable, respect the result. Do not try
  alternate tools or paths to recover restricted content.

## Handle writes conservatively

Reads and writes are distinct. Writes are never implicit.

- Only write when the user's request and the caller's tool permission both
  authorize it. A missing or unknown tool permission means: do not write.
- `save_inbox_note` requires the `brain:write` scope and creates a new note
  under `vault/00-Inbox/`, committed with the calling window as git author. Use
  it for new captured notes rather than editing existing ones.
- `edit_note` requires `brain:write` **and** read access to the target's tier.
  It preserves the note's existing frontmatter unless `overwrite_frontmatter`
  is explicitly `true`. Prefer the default.
- `delete_note` is a tier-0 operation: it requires brady clearance, the
  `brain:write` scope, and `confirm: true`. Never set `confirm: true` unless the
  user explicitly asked to delete that note.
- **Never silently rewrite, reorganize, migrate, or bulk-edit existing Brain
  notes.** Propose changes and let the user direct them.

## Limitations

- No client isolation and no per-client registry (see above).
- Authentication is a static bearer token per window; there is no per-request
  user consent flow.
- The server mirrors a git repo and derived indexes; freshness is bounded by
  the server's refresh interval. Very recent edits may not be visible yet.
- `get_context` never returns full bodies, and `note_contract` never returns
  raw frontmatter.
- The knowledge graph is a mirror of the `ai-coordinator` output; a missing or
  stale graph is a server condition, not something the agent can fix.

## Portability

This file uses the plain `SKILL.md` convention (YAML `name` + `description`
frontmatter, Markdown body) shared by opencode and compatible skill loaders. It
is runtime-agnostic on purpose. How the skill is **installed** into a given
agent is runtime-specific and is documented separately in
[`../README.md`](../README.md). Connecting an agent to the MCP server exposes
the tools but does **not** install this skill.
