# TEMPLATES.md
> Normative ingest template catalog for the agentic wiki.

Related notes:
- [[index]]
- [[schema/RULES]]

## 1. Contract

- This file MUST define ingest templates by source format or structure.
- This file MUST NOT define templates by semantic domain.
- Runtime MUST use this file when registering or building sources.
- Runtime MUST NOT use this file as the source registry.

---

## 2. Allowed Templates

| Template | Match condition | Inputs |
|---|---|---|
| `csv-tabular` | source is a delimited table with headers and rows | `.csv`, `.tsv`, delimited exports |
| `json-structured` | source is JSON with stable keys or nested structure | `.json` |
| `markdown-document` | source is a Markdown document with readable sections | `.md` |
| `html-document` | source is an HTML document requiring text extraction | `.html`, `.htm` |
| `pdf-document` | source is a text-bearing PDF document | `.pdf` |
| `docx-document` | source is a structured Office document | `.docx` |
| `text-document` | source is lightly structured plain text | `.txt`, plain text output |
| `repo-directory` | source is a repository or repository mirror | folder with code, README, or project manifest |
| `workspace-directory` | source is an agent workspace | folder with governance or workspace files |

Template rules:
- `ingest_template` MUST be one of the table values or `custom`.
- Runtime MUST set `template_review_needed: true` when no allowed template matches credibly.
- Runtime MAY use `custom` only when the source cannot be represented by an allowed template.
- Runtime MUST choose `repo-directory` when the directory's primary content is source code or repository metadata.
- Runtime MUST choose `workspace-directory` when the directory's primary content is operational or governance material for an agent workspace.

---

## 3. Matching Order

Runtime MUST select templates in this order:
1. explicit `ingest_template` from an existing canonical manifest
2. explicit `ingest_template_hint` from a remote hint
3. explicit `content_format`
4. file extension
5. content structure
6. generic fallback
7. `custom` plus `template_review_needed: true`

---

## 4. Semantic Tags

Semantic tags MUST describe source domain.
Semantic tags MUST NOT be used as templates.

Non-exhaustive semantic tag examples:
- `architecture`
- `network`
- `ipam`
- `security`
- `paper`
- `runbook`
- `inventory`
- `policy`
- `workspace`
- `codebase`

---

## 5. Catalog Evolution

- Runtime MUST create the intake artifact even when no template matches credibly.
- Runtime MUST set `template_review_needed: true` when no template matches credibly.
- Runtime MAY suggest a new template in the intake artifact.
- Template suggestions MUST be written in the intake artifact body as prose.
- Template suggestions MUST NOT be treated as registered templates until added to this file.
- A new template MUST be added only when the source structure is recurring and the generic fallback is insufficient.
