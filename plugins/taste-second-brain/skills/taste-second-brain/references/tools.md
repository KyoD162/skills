# Tool reference (taste-second-brain)

Verified against `src/second_brain_mcp/tools.py` at server version `0.1.0`.
Every tool returns a single JSON object string with a `status` field. Missing
resources return `{"status": "not_found"}`; write tools without the
`brain:write` scope return `{"status": "denied"}`. Do not invent arguments or
response fields beyond what is listed here.

## Reads

### `get_context`

Bounded context assembly over the whole brain. Identity comes from the
window's bearer token, never from caller fields.

| Argument | Type | Default | Notes |
| --- | --- | --- | --- |
| `query` | string | `""` | Search term. |
| `limit` | integer | `10` | Clamped server-side to `1..25`. |
| `include_recent` | boolean | `false` | Add most recently modified notes. |
| `include_relations` | boolean | `false` | Add graph neighborhood of `query`. Ignored when `query` is empty. |
| `client_scope` | string | `null` | Accepted but ignored; client isolation is not implemented. |

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
      "snippet": "... bounded excerpt; full bodies are never returned ...",
      "modified": "1728000000"
    }
  ],
  "budget": {"limit": 10, "used": 1, "truncated": false, "omitted_count": 0}
}
```

`modified` is present only for items sourced from `include_recent` and is the
filesystem mtime as seconds since epoch, stringified (matching
`list_recent`'s numeric epoch value). Items are
deduplicated by `path`. `snippet` is a bounded excerpt: body-derived snippets
are capped at 240 characters, while search-sourced snippets come from the FTS
highlighter and may vary in length. Full bodies are never returned here.
`client_scope` is accepted but has no effect.

### `search_brain`

Full-text + frontmatter + path search. Matching is lexical: query terms are
AND-ed (with a small synonym/acronym expansion), and a relaxed OR pass is
appended when the strict match set is sparse. Results are BM25-ranked with
`path`/`frontmatter` weighted above `body`, then a small metadata/recency
tie-break. Search covers the whole vault for every authenticated window.

| Argument | Type | Default | Notes |
| --- | --- | --- | --- |
| `query` | string | required | |
| `limit` | integer | `10` | Bounded to `1..50`. |
| `tags` | array of string | `null` | Optional; keep only notes carrying **all** listed tags. |
| `path_prefix` | string | `null` | Optional; keep only notes whose path starts with this prefix (e.g. `99-meetings`). Unsafe prefixes (`..`) return no results. |

```json
{"status": "found", "results": [{"path": "...", "frontmatter": "...", "snippet": "... <b>matched</b> ..."}]}
```

`frontmatter` is a stringified map; `snippet` may include `<b>` / `</b>`
highlight markers and an ellipsis `…`. Filename tokens are searchable because
`path` is indexed.

### `read_note`

| Argument | Type | Notes |
| --- | --- | --- |
| `path` | string | Vault-relative path, e.g. `02-operations/staff-eod-flow.md`. |

```json
{"status": "found", "path": "...", "title": "...", "frontmatter": {"title": "...", "tags": "..."}, "body": "..."}
```

Missing paths return `{"status": "not_found"}`.

### `note_contract`

Read-only Knowledge Contract (v0.1) normalization of one note. Available to
every authenticated window, like `read_note`. The returned `tier` is the
effective (computed) tier, not merely the declared frontmatter value. Raw
frontmatter and `raw_frontmatter_text` are never echoed.

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
  "tier": "tier1",
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

`not_found` when the entity is absent. Only one hop is expanded. Node `path`
values are vault-relative when the graph node can be resolved to a real file.

### `list_recent`

| Argument | Type | Default |
| --- | --- | --- |
| `n` | integer | `10` |

```json
{"status": "found", "notes": [{"path": "...", "title": "...", "modified": 1728000000}]}
```

## Writes

Writes require the `brain:write` scope and are committed with the calling
window as git author. Every current window holds that scope. `not_found` is
returned for missing paths; `{"status": "denied"}` for a missing scope or a
delete without `confirm: true`; `{"status": "error", "message": "..."}` for a
git failure.

### `save_inbox_note`

| Argument | Type |
| --- | --- |
| `title` | string |
| `body` | string |

Creates a new note under `vault/00-Inbox/`.

```json
{"status": "saved", "path": "00-Inbox/2026-10-13 my-title.md"}
```

### `edit_note`

| Argument | Type | Default |
| --- | --- | --- |
| `path` | string | required |
| `body` | string | required |
| `overwrite_frontmatter` | boolean | `false` |

Preserves existing frontmatter unless `overwrite_frontmatter` is `true` (then
`body` must carry the full frontmatter).

```json
{"status": "saved", "path": "...", "changed": true}
```

`changed` is `false` when the content is identical (no commit).

### `delete_note`

| Argument | Type | Default |
| --- | --- | --- |
| `path` | string | required |
| `confirm` | boolean | `false` |

Requires `brain:write` and `confirm: true`. Without `confirm` it returns
`denied` and deletes nothing.

```json
{"status": "deleted", "path": "..."}
```

## Status summary

| `status` | Meaning |
| --- | --- |
| `found` | Read succeeded. |
| `not_found` | Missing resource (or no resolved window). |
| `denied` | Missing write scope or a delete without `confirm: true`. |
| `saved` | Write committed (or content unchanged for `edit_note`). |
| `deleted` | Deletion committed. |
| `error` | Server/git failure; `message` may be present. |
