# sources/raw/

Related notes:
- [[index]]
- [[schema/RULES]]
- [[sources/intake/README]]

## Contract

- This folder MUST contain local raw source files or local raw source directories.
- This folder MUST be treated as `Matter Layer`.
- Runtime MUST read this folder during local bootstrap.
- Runtime MUST NOT edit files or directories in this folder.
- Runtime MUST NOT treat files in this folder as canonical manifests.

## Local Source Unit

- Each top-level entry in `sources/raw/`, except `README.md`, is one local raw source.
- A top-level file is one source.
- A top-level directory is one source.
- Files inside a top-level source directory belong to that source and are not separate sources by default.

Examples:

- `sources/raw/doc.txt` -> one local source
- `sources/raw/harness-engineering/` -> one local source
- `sources/raw/sub-a/` and `sources/raw/sub-b/` -> two local sources

## Local Bootstrap Flow

For each new or changed local source, Runtime MUST:
1. read the source from `sources/raw/`
2. analyze the source
3. generate `sources/intake/intake-{logical_name}.md`
4. generate or update `sources/source-{logical_name}.md`
5. leave generated knowledge creation to build

## State Rules

- If a local source changes, Runtime MUST set the canonical manifest `lifecycle_state` to `changed`.
- If a local source disappears while its canonical manifest still exists, Runtime MUST set `lifecycle_state` to `removed`.
- If reconcile is requested for a removed local source, Runtime MUST set `lifecycle_state` to `forget-pending`.
- Remote sources MUST NOT pass through this folder.
