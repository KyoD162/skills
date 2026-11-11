# Tool reference (taste-second-brain)

Verified against `src/second_brain_mcp/tools.py` at server version `0.1.0`,
policy version `2.0.0`. Every tool returns a single JSON object string with a
`status` field. Missing resources return `{"status": "not_found"}`; write tools
without the `brain:write` scope return `{"status": "denied"}`. Do not invent
arguments or response fields beyond what is listed here.

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
{"status": "found", "path": "...", "title": "...", "revision": "<sha256 of the raw file bytes>", "frontmatter": {"title": "...", "tags": "..."}, "body": "..."}
```

Missing paths return `{"status": "not_found"}`. `revision` is the content hash
to pass to `edit_note` and `move_note` as `expected_revision`.

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

### `list_folders`

Distinct vault-relative folders that contain at least one note, sorted. Use it
to file a document where it belongs instead of piling up in `00-Inbox`. No
arguments.

```json
{"status": "found", "folders": ["00-Inbox", "01-Operator-Bibles/Operations"]}
```

`list_folders` lists note folders only and is not a complete inventory. For a
complete, bounded file manifest use `vault_manifest`.

### `vault_manifest`

The complete, bounded file inventory of the vault. This is the migration
inventory surface: it is **not** capped by search result limits, and it covers
every file (notes, attachments, and other files), not only indexed notes.
Read-only; available to every authenticated window.

| Argument | Type | Default | Notes |
| --- | --- | --- | --- |
| `limit` | integer | `500` | Entries per page, bounded to `1..500`. |
| `cursor` | string | `null` | `next_cursor` from the previous page. |
| `path_prefix` | string | `null` | Narrow to one subtree, e.g. `04-Project-Atlas`. Unsafe prefixes (`..`, `a//b`) return `error`. |
| `include_sha256` | boolean | `true` | Set `false` to skip hashing large inventories. |

```json
{
  "status": "found",
  "entries": [
    {"path": "02-Operations/staff-eod-flow.md", "bytes": 842, "kind": "note", "sha256": "..."}
  ],
  "truncated": true,
  "next_cursor": "02-Operations/staff-eod-flow.md"
}
```

Entries are path-ordered and stable across pages: no gaps, no duplicates.
`kind` is `note`, `attachment`, or `file`. `sha256` is the hash of the raw file
bytes and equals `read_note`'s `revision`, so it can be passed straight to
`move_note` as `expected_revision`. `truncated` is `false` on the last page.

## Writes

Writes require the `brain:write` scope and are committed with the calling
window as git author. Every current window holds that scope. `not_found` is
returned for missing paths; `{"status": "denied"}` for a missing scope or a
the disabled delete lane; `{"status": "error", "message": "..."}` for a
git failure.

Every write response carries a **write receipt** (`receiptVersion: 2`):

```json
{"receiptVersion": 2, "kind": "write", "tool": "edit_note", "actor": "claude-code",
 "policyVersion": "2.0.0", "path": "02-Operations/x.md", "sha256": "...",
 "previousSha256": "...", "changed": true, "recordedAt": "2026-11-11T12:00:00Z"}
```

`actor` is the calling window. `sha256` is the content hash after the write.
`previousSha256`, `dedupe`, and `changed` appear only where they apply.

**Destination policy.** Every write is checked against the versioned policy.
A destination under an allowed root is accepted; an unknown root returns
`error` (`not allowed`), a protected root returns `error` (`protected`), and a
*restricted* destination (`03-Contracts-Drop`) returns `denied` for any window
other than the one named in the policy (`brady`).

**Graph exclusion.** `13-Health-Macros` and `04-Project-Atlas/Health-Macros`
never enter `query_graph` or graph-derived context. They stay readable through
`read_note` and findable through `search_brain`; exclusion is a graph boundary,
not a read boundary.

### `save_inbox_note`

| Argument | Type |
| --- | --- |
| `title` | string |
| `body` | string |
| `policy_version` | string | `null` |

Creates a new note under `vault/00-Inbox/`.

```json
{"status": "saved", "path": "00-Inbox/2026-10-13 my-title.md"}
```

### `save_document`

| Argument | Type | Default |
| --- | --- | --- |
| `title` | string | required |
| `body` | string | required |
| `source` | string | required |
| `tags` | list of strings | `null` |
| `source_sha256` | string | `null` |
| `converter` | string | `null` |
| `folder` | string | `null` | Allowed policy root. |
| `category` | string | `null` | Must map to the destination root when supplied. |
| `policy_version` | string | `null` | Server policy version pin. |

Creates a document note under `vault/00-Inbox/` from a machine-converted
source (PDF/DOCX/... → Markdown). Records conversion provenance instead of
authored metadata: `fidelity: converted`, the named `source`, and optional
`source_sha256` + `converter` for reproducibility. The filename is
content-addressed (`{slug}-{digest8}.md`, no capture date — `created`
carries it), so the same source under the same title always lands on the
same path on any day or machine; a re-ingest overwrites rather than
duplicates. A different title for the same source creates a new note.
`source_sha256` must be a 64-character hex digest; `source` must be
non-empty. Tags always include `from-ingest`.

```json
{"status": "saved", "path": "00-Inbox/informe-q3-9f2c4e1a.md"}
```

Agents that already hold Markdown can call this directly. The repo's
`sb-ingest` CLI, `--watch` folder lane, and local web UI wrap it with
conversion, an editable preview, and a machine-local journal (see
`runbooks/server-operations.md`); they all push through this tool, never
git.

### `save_attachment`

| Argument | Type | Default |
| --- | --- | --- |
| `filename` | string | required |
| `content_b64` | string | required |
| `source` | string | required |
| `caption` | string | `null` |
| `source_sha256` | string | `null` |

Stores one binary figure (image) from a converted document under
`vault/90-Attachments/`, committed with the calling window as git author.
The filename is content-addressed from the attachment bytes
(`{slug}-{digest8}.{ext}`), so pushing the same image twice lands on the
same path and is reported as a dedupe no-op (`"dedup": true`), never a
duplicate. Attachments are invisible to `search_brain` and `list_recent`
on purpose — only the notes that embed them are indexed; provenance lives
in the embedding note (`source`, `source_sha256`) and in the git commit
message. Allowed extensions: png/jpg/jpeg/gif/webp/svg, base64-encoded,
up to 10 MB. The response includes a ready-to-paste `markdown` embed.

```json
{"status": "saved", "path": "90-Attachments/chart-9f2c4e1a.png",
 "sha256": "...", "size_bytes": 8421, "dedup": false,
 "markdown": "![chart](90-Attachments/chart-9f2c4e1a.png)"}
```

### `edit_note`

| Argument | Type | Default |
| --- | --- | --- |
| `path` | string | required |
| `body` | string | required |
| `overwrite_frontmatter` | boolean | `false` |
| `expected_revision` | string | `null` |

Preserves existing frontmatter unless `overwrite_frontmatter` is `true` (then
`body` must carry the full frontmatter). `read_note` returns a SHA-256
`revision`; pass it as `expected_revision` to prevent overwriting a newer
edit. A stale revision returns `conflict`.

```json
{"status": "saved", "path": "...", "changed": true}
```

`changed` is `false` when the content is identical (no commit).

### `move_note`

The governed migration primitive. This is the **only** sanctioned way to
relocate a note: a move is revision-checked, collision-refusing, idempotent,
policy-checked, and receipted.

| Argument | Type | Default | Notes |
| --- | --- | --- | --- |
| `source` | string | required | Vault-relative path of the note to move. |
| `destination` | string | required | Vault-relative target path, including filename. |
| `expected_revision` | string | required | Current sha256 of the source (`read_note` `revision` or `vault_manifest` `sha256`). |
| `batch_id` | string | required | Filename-safe id (`[A-Za-z0-9][A-Za-z0-9._-]{0,63}`) naming the batch ledger. |
| `policy_version` | string | required by the server | Must match the server policy (`2.0.0`). |
| `dry_run` | boolean | `false` | Return the planned move and its checks; write nothing. |

Success:

```json
{"status": "moved", "path": "01-Operator-Bibles/Operations/x.md",
 "receipt": {"receiptVersion": 2, "kind": "move", "batchId": "wave-2-20261111",
   "policyVersion": "2.0.0", "sourcePath": "02-Operations/x.md",
   "sourceSha256": "...", "destinationPath": "01-Operator-Bibles/Operations/x.md",
   "destinationSha256": "...", "actor": "claude-code",
   "recordedAt": "2026-11-11T12:00:00Z", "status": "moved"}}
```

The move and its receipt land in **one commit**: the rename plus the batch
ledger at `_meta/migrations/receipts/move-<batch_id>.json`. Retrying a
completed move returns `already_moved` with the original receipt; it never
creates a duplicate and never makes a second commit. `dry_run` returns
`planned` with `checks: {source_exists, revision_matches, destination_allowed,
destination_free}`.

Conflict statuses are explicit and never collapsed:

| Status | Meaning |
| --- | --- |
| `not_found` | Source missing, or an unsafe/traversal path (answered anonymously). |
| `already_moved` | This batch already moved this source; the original receipt is returned. |
| `destination_exists` | The target is occupied. Nothing is overwritten. |
| `revision_mismatch` | `expected_revision` is stale; the response carries `actual_revision`. |
| `denied` | Missing write scope, or a restricted destination for this window. |
| `error` | Policy rejection (protected/unknown destination), bad `batch_id`, version mismatch, or git failure. |

### `patch_note`

The surgical edit primitive for literal find/replace rewrites. Use it instead of
`edit_note` when the change is a targeted string replacement (a link rewrite, a
path fix, a corrected name): the file's frontmatter, formatting, and every
untouched byte are preserved exactly.

| Argument | Type | Default | Notes |
| --- | --- | --- | --- |
| `path` | string | required | Vault-relative path of the note to patch. |
| `replacements` | array | required | Each item is `{ "find": string, "replace": string, "count"?: integer }`. `find` must be non-empty; `replace` may be empty. `count` (>= 1) limits how many occurrences of that `find` change; omit to replace all. |
| `expected_revision` | string | required | Current revision of the note (`read_note` `revision` or `vault_manifest` `sha256`). |
| `policy_version` | string | required by the server | Must match the server policy (`2.0.0`). |
| `batch_id` | string | `null` | Optional filename-safe batch label. |
| `dry_run` | boolean | `false` | Validate and compute the planned hash; write nothing. |

The whole patch is validated before any byte changes: if any `find` string is
absent and not already replaced, the call returns `no_match` and the file is
untouched (no half-applied patch).

Success:

```json
{"status": "saved", "path": "02-People/note.md", "changed": true, "replacements": 3,
 "receipt": {"receiptVersion": 2, "kind": "write", "tool": "patch_note", "actor": "claude-code",
  "policyVersion": "2.0.0", "path": "02-People/note.md", "sha256": "...",
  "previousSha256": "...", "changed": true, "recordedAt": "2026-11-11T12:00:00Z"}}
```

Statuses:

| Status | Meaning |
| --- | --- |
| `saved` | Patch committed; `changed` is `true` and `replacements` counts applied occurrences. |
| `planned` | `dry_run` only: the patch would change the file; carries `sha256` of the would-be content. Nothing written. |
| `already_applied` | A retry: no `find` matched and every `replace` is already present. `changed` is `false`, no commit. |
| `no_match` | At least one `find` string is absent. Nothing written; the response lists `missing`. |
| `revision_mismatch` | `expected_revision` is stale; the response carries `actual_revision`. |
| `denied` | Missing write scope, or a restricted destination for this window. |
| `not_found` | Note missing or path unsafe. |
| `error` | Policy rejection (protected/unknown destination, missing policy version), bad input, or git failure. |

`patch_note` is destination-checked like every other write (protected/unknown
roots rejected, `03-Contracts-Drop` restricted to `brady`) and returns a write
receipt on `saved`.

### `delete_note`

| Argument | Type | Default |
| --- | --- | --- |
| `path` | string | required |
| `confirm` | boolean | `false` |

Deletion is disabled until an independent approval service exists. The
`confirm` parameter is retained for compatibility but is not sufficient
authorization; the tool returns `denied` and deletes nothing.

```json
{"status": "deleted", "path": "..."}
```

## Status summary

| `status` | Meaning |
| --- | --- |
| `found` | Read succeeded. |
| `not_found` | Missing resource (or no resolved window). |
| `denied` | Missing write scope, restricted destination, or deletion is unavailable without independent approval. |
| `saved` | Write committed (or content unchanged for `edit_note`). |
| `moved` | Move committed with its receipt. |
| `already_moved` | Idempotent retry: this batch already moved this source; original receipt returned. |
| `already_applied` | Idempotent retry of `patch_note`: the replacements are already present; no commit. |
| `planned` | `dry_run` only: the operation is valid and would succeed; nothing was written. |
| `no_match` | `patch_note` refused: at least one `find` string is absent. Nothing written. |
| `destination_exists` | Move refused: the target is occupied. Nothing overwritten. |
| `revision_mismatch` | Move/patch refused: `expected_revision` is stale. |
| `conflict` | `edit_note` refused: `expected_revision` is stale. |
| `deleted` | Reserved for a future approved deletion lane. |
| `error` | Server/git failure or policy rejection; `message` may be present. |
