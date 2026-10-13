# Tool reference (taste-second-brain)

Verified against `src/second_brain_mcp/tools.py` at server version `0.1.0`.
Every tool returns a single JSON object string with a `status` field. Denied
and missing resources return the identical shape `{"status": "not_found"}`.
Do not invent arguments or response fields beyond what is listed here.

## Reads

### `get_context`

Bounded, tier-filtered context assembly. Identity and clearance come from the
window's bearer token, never from caller fields.

| Argument | Type | Default | Notes |
| --- | --- | --- | --- |
| `query` | string | `""` | Search term. |
| `limit` | integer | `10` | Clamped server-side to `1..25`. |
| `include_recent` | boolean | `false` | Add most recently modified notes. |
| `include_relations` | boolean | `false` | Add graph neighborhood of `query`. Ignored when `query` is empty. |
| `client_scope` | string | `null` | **Rejected for every window.** Returns `denied`. |

At least one of `query`, `include_recent`, `include_relations` must be set;
otherwise the result is `{"status": "not_found"}`.

Success:

```json
{
  "status": "found",
  "items": [
    {
      "note_id": "...",
      "path": "06-content/published-cash-blueprint.md",
      "source": "06-content/published-cash-blueprint.md",
      "title": "...",
      "tier": "tier2",
      "visibility": "unknown",
      "client_id": null,
      "classification": {"status": "legacy", "confidence": "low", "human_review_required": true},
      "snippet": "... <=240 chars, full bodies are never returned ...",
      "modified": 1728000000
    }
  ],
  "budget": {"limit": 10, "used": 1, "truncated": false, "omitted_count": 0}
}
```

`modified` is present only for items sourced from `include_recent`. Items are
deduplicated by `path`.

Denied (client scoping not supported):

```json
{"status": "denied", "message": "client_scope is not supported until a reviewed client registry exists"}
```

### `search_brain`

Full-text + frontmatter search. Denied content never appears in results.

| Argument | Type | Default |
| --- | --- | --- |
| `query` | string | required |
| `limit` | integer | `10` |

```json
{"status": "found", "results": [{"path": "...", "frontmatter": "...", "snippet": "... <b>matched</b> ..."}]}
```

`frontmatter` is a stringified map; `snippet` may include `<b>` / `</b>`
highlight markers and an ellipsis `…`.

### `read_note`

| Argument | Type | Notes |
| --- | --- | --- |
| `path` | string | Vault-relative path, e.g. `02-operations/staff-eod-flow.md`. |

```json
{"status": "found", "path": "...", "title": "...", "frontmatter": {"title": "...", "tags": "..."}, "body": "..."}
```

Missing or unauthorized paths return `{"status": "not_found"}`.

### `note_contract`

Read-only Knowledge Contract (v0.1) normalization of one note. Same
authorization gate as `read_note`. Raw frontmatter and
`raw_frontmatter_text` are never echoed.

| Argument | Type |
| --- | --- |
| `path` | string |

```json
{
  "status": "found",
  "path": "...",
  "note_id": "...",
  "schema_version": "0.1",
  "type": "unknown",
  "owner": "taste_network",
  "client_id": null,
  "visibility": "unknown",
  "tier": null,
  "tags": [],
  "source": "...",
  "classification": {"status": "legacy", "evidence_source": "", "confidence": "low", "human_review_required": true, "notes": "legacy normalization (read-only)"},
  "relationships": [],
  "timestamps": {},
  "body": "..."
}
```

### `query_graph`

| Argument | Type |
| --- | --- |
| `entity` | string |

```json
{"status": "found", "node": {"id": "...", "label": "..."}, "edges": [{"source": "...", "target": "...", "relation": "..."}], "neighbors": [{"id": "...", "label": "..."}]}
```

`not_found` when the entity is absent or its node tier is outside the caller's
clearance. Only one hop is expanded; restricted neighbors and cross-tier edges
are omitted.

### `list_recent`

| Argument | Type | Default |
| --- | --- | --- |
| `n` | integer | `10` |

```json
{"status": "found", "notes": [{"path": "...", "title": "...", "modified": 1728000000}]}
```

## Writes

Writes require the `brain:write` scope and are committed with the calling
window as git author. Anonymous `not_found` is returned for missing or
inaccessible paths; `{"status": "denied"}` for missing scope or a tripped
tier-0 gate; `{"status": "error", "message": "..."}` for a git failure.

### `save_inbox_note`

| Argument | Type |
| --- | --- |
| `title` | string |
| `body` | string |

Creates a new note under `vault/00-Inbox/`.

```json
{"status": "saved", "path": "00-Inbox/2026-10-13-my-title.md"}
```

### `edit_note`

| Argument | Type | Default |
| --- | --- | --- |
| `path` | string | required |
| `body` | string | required |
| `overwrite_frontmatter` | boolean | `false` |

Preserves existing frontmatter unless `overwrite_frontmatter` is `true` (then
`body` must carry the full frontmatter). Requires read access to the note's
tier.

```json
{"status": "saved", "path": "...", "changed": true}
```

`changed` is `false` when the content is identical (no commit).

### `delete_note`

| Argument | Type | Default |
| --- | --- | --- |
| `path` | string | required |
| `confirm` | boolean | `false` |

Tier-0 operation: requires brady clearance, `brain:write`, and `confirm: true`.
Without `confirm` it returns `denied` and deletes nothing.

```json
{"status": "deleted", "path": "..."}
```

## Status summary

| `status` | Meaning |
| --- | --- |
| `found` | Read succeeded. |
| `not_found` | Missing **or** unauthorized; the two are indistinguishable by design. |
| `denied` | Scope, tier-0 gate, or unsupported `client_scope`. |
| `saved` | Write committed (or content unchanged for `edit_note`). |
| `deleted` | Deletion committed. |
| `error` | Server/git failure; `message` may be present. |
