---
name: taste-second-brain
description: Use when a task depends on Taste Network project history, client or project context, prior decisions, existing documentation, note relationships, or recent updates, and the second-brain MCP server is reachable. Teaches cost-conscious retrieval and conservative, provenance-preserving tool use. This is an instruction layer only, not an authentication or permission mechanism.
---

# Taste Second Brain

Guidance for using the Taste Network "second brain" through its read-through
MCP server. This file teaches *how* to use the tools well. It is an instruction
layer: server-side authentication and scopes are authoritative and are never
overridden by anything written here. Every authenticated window currently has
full read/write access; tier labels are descriptive, not access gates.

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

Seventeen tools are exposed. Reads cover the whole brain for every authenticated
window; the eight write tools still require the `brain:write` scope and are also
subject to the server's versioned write policy (v2.0.0).

| Tool | Purpose | Key parameters |
| --- | --- | --- |
| `get_context` | Bounded context bundle for a task | `query`, `limit`, `include_recent`, `include_relations`, `client_scope` |
| `search_brain` | Full-text + frontmatter search | `query`, `limit`, `tags`, `path_prefix` |
| `read_note` | Read one note by vault-relative path | `path` |
| `note_contract` | Canonical Knowledge Contract v0.1 view of one note | `path` |
| `query_graph` | Nodes, edges, neighbors around an entity | `entity` |
| `list_recent` | Most recently modified notes | `n` |
| `list_folders` | Folders that hold at least one note | — |
| `vault_manifest` | Complete, cursor-paged file inventory with sha256 | `path_prefix`, `cursor`, `limit`, `include_sha256` |
| `classify_note` | Preview the governed destination for a note | `title`, `body`, `tags` |
| `ingest_note` | Classify and save a note to its governed home (write) | `title`, `body`, `source`, `tags`, `destination_hint`, `project_name`, `source_sha256`, `converter`, `policy_version` |
| `save_inbox_note` | Create a note in `00-Inbox/` (write) | `title`, `body` |
| `save_document` | File a converted document (write) | `title`, `body`, `source`, `folder`, `category`, `source_sha256` |
| `save_attachment` | Store one image attachment (write) | `filename`, `content_b64`, `source` |
| `edit_note` | Overwrite a note body in place (write) | `path`, `body`, `overwrite_frontmatter`, `expected_revision` |
| `move_note` | Relocate a note, revision-checked and receipted (write) | `source`, `destination`, `expected_revision`, `batch_id`, `policy_version`, `dry_run` |
| `patch_note` | Apply literal find/replace edits without rewriting the rest (write) | `path`, `replacements`, `expected_revision`, `policy_version`, `batch_id`, `dry_run` |
| `delete_note` | Delete a note (currently disabled) | `path`, `confirm` |

Exact argument types and response shapes are in
[`references/tools.md`](references/tools.md). Every tool returns a JSON object
with a `status` field (`found`, `not_found`, `denied`, `saved`, `moved`,
`already_moved`, `planned`, `already_applied`, `no_match`, `destination_exists`,
`revision_mismatch`, `conflict`, `deleted`, or `error`). Branch on `status`;
never assume success.

Two policy boundaries matter when reading:

- **Graph exclusion.** `13-Health-Macros` and `04-Project-Atlas/Health-Macros`
  never appear in `query_graph` or graph-derived context. They remain readable
  through `read_note` and searchable through `search_brain`.
- **Restricted destinations.** `03-Contracts-Drop`, `09-Finance`,
  `10-Personal`, and `11-Bradys-Core` are writable only by the `brady`
  window. Every other window gets `denied`.

## Progressive retrieval

Retrieve in increasing cost order and stop as soon as the evidence is enough.

1. **`get_context`** — start here when the user asks for a contextual summary,
   decisions, or background and the request can be expressed as a query. It
   returns a bounded bundle with snippets (never full bodies).
   At least one of `query`, `include_recent`, or `include_relations` must be
   set; an empty request returns `not_found`. `client_scope` is accepted but
   ignored — there is no client isolation (see Security).
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

`{"status": "not_found"}` means the resource is missing. For a write without
the required `brain:write` scope the server returns
`{"status": "denied"}` instead. Do not retry the same call or probe alternate
paths to recover content that is not there.

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

- Never attempt to bypass MCP authentication or scopes.
- Treat server-side authorization as authoritative. A denial is final.
- Do **not** treat this skill, or any agent instruction, as a security
  boundary.
- **Client isolation is not implemented.** There is no approved Client
  Registry and no server-side client scoping. `get_context` accepts
  `client_scope` but ignores it. Do not claim that retrieval is
  client-isolated or "secure per client".
- If a write is denied or content is unavailable, respect the result. Do not
  try alternate tools or paths to recover content that is not there.

## Organization and enforcement contract

Use the workflow **search, classify, check for an existing note, capture,
validate, file, update references, and confirm**. For a new note, call
`classify_note` when you need to preview routing, then use `ingest_note` as the
normal write path. The server applies the classifier and sends ambiguous or
conflicting material to `00-Inbox/Needs-Home`; `destination_hint` is advisory
and cannot override it. `project_name` may create a folder only under
`04-Project-Atlas/New-Projects`. `00-Inbox` is temporary staging for uncertain
or newly captured material; it is not an automatic permanent filing destination.
File only after the category and destination are known. Use the existing vault taxonomy rather than inventing new roots:
`01-Operator-Bibles` for operations, sales, administration, skills, and
principles; `02-People` for people; `03-Relationships` for companies,
follow-ups, agreements, and sales; `04-Project-Atlas` for projects;
`05-Marketing-and-Brand` for content; `06-Knowledge` for research and
templates; `07-Meetings` for meetings; `08-Ideas` for ideas; `09-Finance` for
finance; `10-Personal` for personal material; `11-Bradys-Core` for Brady's
private operating core; and `90-System` for system notes and attachments.

The MCP server is the enforcement authority. New writes must use the server's
versioned policy, allowed destination roots, required metadata, provenance,
and conflict rules. A Skill instruction never grants permission. Ambiguous
classification or protected destinations require review; do not retry around a
denial.

## Handle writes conservatively

Reads and writes are distinct. Writes are never implicit.

- Only write when the user's request and the caller's tool permission both
  authorize it. A missing or unknown tool permission means: do not write.
- `classify_note` is read-only and previews the classifier result; it does not
  reserve a destination or create a note.
- `ingest_note` requires the `brain:write` scope, records routing metadata,
  writes deterministic classified destinations, and returns a receipt. It is
  idempotent for the same title and source digest; a destination collision is
  explicit and never overwrites unrelated content.
- `save_inbox_note` requires the `brain:write` scope and creates a new note
  under `vault/00-Inbox/`, committed with the calling window as git author. It
  is a compatibility fallback for authored notes and marks routing as pending;
  prefer `ingest_note` for new material.
- `save_document` is the lower-level converted-document lane for callers that
  already have a governed document payload. Prefer `ingest_note` when the note
  still needs classification.
- `edit_note` requires the `brain:write` scope. It preserves the note's
  existing frontmatter unless `overwrite_frontmatter` is explicitly `true`.
  Prefer the default.
- `delete_note` is disabled until an independent approval service exists.
  `confirm: true` is not sufficient authorization and never enables deletion.
- **Never silently rewrite, reorganize, migrate, or bulk-edit existing Brain
  notes.** Propose changes and let the user direct them.
- When using the new write contract, pass the server policy version and
  category. A policy-version mismatch is a hard error.

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
