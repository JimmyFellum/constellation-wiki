# sources/intake/

Related notes:
- [[index]]
- [[schema/RULES]]
- [[sources/raw/README]]
- [[sources/remote/README]]

## Contract

- This folder MUST contain LLM-generated intake artifacts.
- This folder MUST be treated as `Formation Layer`.
- Intake artifacts MUST use `intake-{logical_name}.md`.
- Intake artifacts MUST make source analysis observable.
- Intake artifacts MUST NOT be treated as canonical manifests.
- Humans MUST NOT create intake artifacts by hand.
- Runtime MUST overwrite the intake artifact on each bootstrap of the same source.
- Runtime MAY delete an intake artifact after the matching canonical manifest exists.

## Required Intake Fields

Each intake artifact MUST contain:
- `logical_name`
- `intake_source_kind`
- `detected_format`
- `detected_template`
- `template_confidence`
- `semantic_tags`
- `proposed_source_mode`
- `proposed_source_locator`
- `proposed_raw_path`
- `template_review_needed`

Canonical source registry files MUST use:
- `sources/source-{logical_name}.md`
