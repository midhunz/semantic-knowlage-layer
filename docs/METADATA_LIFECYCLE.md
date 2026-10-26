# How table and column metadata changes

Two kinds of metadata live on every table and column, with different owners:

| | Owned by | Examples | Changed by |
|---|---|---|---|
| **Technical** | the lake | name, type, nullable, partitions, row count | **Sync** (never by hand) |
| **Semantic** | people | description, grain, role, synonyms, allowed values, Arabic text, PII flag | Stewards (UI, bulk edit, column dictionary, CSV) |

Sync never overwrites semantic metadata. Agents only ever read **published** tables.

## 1. When the lake changes (sync)

| Event | Result |
|---|---|
| New table | Created as `draft`, flagged *needs review*. Invisible to agents. |
| New column on a table people already know | **Quarantined**: hidden from agents until a steward releases it. |
| New column whose name looks sensitive (`email`, `national_id`, `iban`…) | **Quarantined**, even on a brand-new table. Patterns are editable in Settings. |
| Column type changed | Type updates at once; the column and table are flagged *needs review*. |
| Column / table dropped | Marked `removed` (never deleted), hidden from agents. Documentation is kept. |

**Quarantine queue** (sidebar → *Quarantine*): release a column, or *release as personal data* so it is masked (or hidden entirely, per Settings). Releasing is applied immediately. Joins through a hidden column are never shown to agents.

## 2. When a person edits (draft → published)

* **Draft / reviewed tables** — edits apply directly; nobody is reading them.
* **Published tables** — semantic edits are **staged** in one *pending revision* per table. Agents keep reading the live version. The editor shows pending values (marked *unpublished*) and a bar: *"3 unpublished changes · Agents still see version 4 · Review & publish"*.
* A steward reviews the **diff** (old → new), optionally writes a message, and **publishes** it: the changes go live as a new **version** (v5), a `table.updated` webhook fires, and the audit log records who approved it.
* **Discard** drops the pending changes. Setting a field back to its live value withdraws it automatically.

What stays **live** (not staged), because it is a review action or a safety tightening:

| Always immediate | Why |
|---|---|
| Status changes (publish / unpublish), *needs review* flag | They are the review workflow itself |
| Quarantine and release | Access decisions |
| Marking a column **PII** | Delaying a protection would be wrong. (Un-marking PII *is* staged.) |

Unpublishing a table with pending changes applies them first (nobody reads it any more) and records a version. Editing while unpublished, then re-publishing, records a new version if the content changed.

## 3. Versions, history and restore

Every published version stores a full snapshot. **History** tab: see what each version changed and who published it. **Stage a restore** brings an old version's content back as a pending revision — it is reviewed and published like any other change (restoring on a draft applies at once). Tables published before this feature get a baseline version automatically the first time they are edited.

## 4. At scale

* **Pending changes** page: every table with unpublished edits; select many and publish or discard together. Tables that fail the publishing rules are skipped and reported, not fatal.
* Bulk edits, column-dictionary "apply to all" and CSV import all follow the same rules: published tables stage, drafts apply.

## 5. Settings that shape it (Settings → General)

* **Sensitive column names** — the quarantine keyword list.
* **Require a second person to approve changes** — the publisher may not be one of the editors (turn on only with ≥ 2 stewards).
* **Publishing rules** — *review before publishing* and *minimum documentation %* apply to a table's first publication **and** to the result of every revision.

## What is not staged (yet)

Metrics, glossary terms, schema descriptions, relationships and **dimensions** are still edited live (dimensions are audited and fire a `dimension.updated` webhook). Technical changes made by sync are not versioned, and sync does not write audit rows.
