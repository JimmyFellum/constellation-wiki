# sources/remote/

Related notes:
- [[index]]
- [[schema/RULES]]
- [[sources/intake/README]]

## Contract

- This folder MUST contain remote source hints.
- This folder MUST be treated as `Matter Layer` locator boundary.
- Runtime MUST read this folder during remote bootstrap.
- Runtime MUST NOT treat files in this folder as canonical manifests.
- Runtime MUST NOT create a canonical manifest for an unreachable remote source.

## File Naming

Remote hint files MUST use:
- `remote-{logical_name}.md`

## Remote Hint Template

```yaml
---
title: "[SOURCE-TITLE]"
type: source-remote-hint
logical_name: source-placeholder
source_mode: external-file
source_locator: "[REMOTE-LOCATOR]"
content_format: auto
ingest_template_hint: auto
semantic_tags: []
forget_policy: mark-removed-then-reconcile
reach_via: auto
credential_ref: "none"
hint_status: active
tags: [source-remote-hint, remote]
---
```

Field rules:
- Placeholder values MUST be replaced before Runtime uses the hint.
- `source_mode` MUST be `external-file`, `external-dir`, or `repo-mirror`.
- `source_locator` MUST contain a locator reachable by Runtime.
- `content_format` MUST use the enum in [[schema/RULES]].
- `ingest_template_hint` MUST be `auto` or a template in [[schema/TEMPLATES]].
- `credential_ref` MUST be `none` when no credential profile is required.
- `credential_ref` MUST be a symbolic reference and MUST NOT contain credential values when a credential is required.
- `hint_status` MUST be `active` or `disabled`.

## Remote Bootstrap Flow

If the remote source is reachable, Runtime MUST generate:
- `sources/intake/intake-{logical_name}.md`
- `sources/source-{logical_name}.md`

If the remote source is unreachable, Runtime MUST:
- not generate the canonical manifest
- append the reachability issue to [[log]]
