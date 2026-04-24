# RULES.md
> Primary build contract for the agentic wiki.
> Version: 4.8 - 2026-04-14

## 0. Normative Terms

- `MUST` means required.
- `MUST NOT` means forbidden.
- `MAY` means allowed but not required.
- `Builder` means the build agent governed by this file.
- `Runtime` means Builder execution.
- `source-heartbeat` means a scheduled bootstrap invocation.
- `no-op` means a runtime invocation completed without source, build, or correction work.
- `t0` means the Void State: no generated knowledge has been fixed yet.
- Structured fields MUST override prose.
- Canonical manifests MUST override intake artifacts.
- Intake artifacts MUST override ad hoc textual inference.

Builder responsibilities:
- register observable sources
- create and update Formation artifacts
- materialize Constellation pages from canonical manifests
- record touched artifacts in Formation for Reviewer QC

Builder MUST NOT perform Reviewer QC.

---

## 1. Layer Contract

| Layer                 | Definition                        | Runtime role                                  | Repository projection                                                             |
| --------------------- | --------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------- |
| `Mystery`             | external principle                | MUST NOT be loaded during runtime             | `.mystery/`                                                                       |
| `Void State`          | no generated knowledge exists     | MUST contain no Constellation roots           | absence of `entities/`, `concepts/`, `playbooks/`, `synthesis/`                   |
| `Genesis Layer`       | internal generative law           | MUST define allowed forms and workflows       | `schema/`                                                                         |
| `Matter Layer`        | observable source boundary        | MUST contain source inputs or locators        | `sources/raw/`, `sources/remote/`                                                 |
| `Formation Layer`     | generated control and trace       | MUST record classification, state, and audit  | `index.md`, `log.md`, `absorb_log.json`, `sources/intake/`, `sources/source-*.md` |
| `Constellation Layer` | generated knowledge and relations | MUST exist only after build creates knowledge | `entities/`, `concepts/`, `playbooks/`, `synthesis/`                              |

Layer laws:
- Genesis MUST define possible form, not concrete generated knowledge.
- Matter MUST be observed and MUST NOT be edited by Runtime.
- Formation MUST record how Matter is classified, traced, and transformed.
- Constellation MUST be generated from Matter through Formation.
- Entity categories MUST be source-derived; they MUST NOT be pre-materialized at `t0`.

---

## 2. Runtime Load Order

Runtime MUST load:
1. [[schema/RULES]]
2. [[schema/TEMPLATES]] only when source registration or build is involved

Runtime MUST NOT load:
- `.mystery/`
- [[schema/PROMPT-BUILD]] as a generation contract
- [[schema/PROMPT-CHECK-SOURCES]] as a generation contract
- [[schema/CONTROL]]
- [[schema/PROMPT-CONTROL]]
- non-canonical hidden tool folders
- generated knowledge roots before they exist
- schema files not listed above

Builder invocation prompts live in [[schema/PROMPT-BUILD]].
Source heartbeat invocation prompts live in [[schema/PROMPT-CHECK-SOURCES]].
Reviewer prompts and QC rules live in [[schema/PROMPT-CONTROL]] and [[schema/CONTROL]].
Evaluator prompts live in [[schema/PROMPT-EVAL]].
Builder MUST follow this file after invocation.
Builder MUST NOT use reviewer control files as generation instructions.

---

## 3. Root Contract

Visible root entries required at `t0`:

| Root entry | Layer | Meaning |
|---|---|---|
| `schema/` | `Genesis Layer` | internal generative law |
| `sources/` | `Matter Layer` plus source-side Formation boundary | source inboxes and source control area |
| `index.md` | `Formation Layer` | catalog scaffold |
| `log.md` | `Formation Layer` | operation timeline scaffold |
| `absorb_log.json` | `Formation Layer` | structured audit scaffold |

Visible generated roots:
- `entities/`
- `concepts/`
- `playbooks/`
- `synthesis/`

Root rules:
- Visible generated roots MUST NOT exist at `t0`.
- A generated root MUST be created only when build creates the first page inside it.
- Any visible non-hidden root entry not listed in this section MUST be removed or explicitly added to this schema.
- Hidden folders MAY exist only when they are tool-specific or explicitly declared non-runtime.
- Hidden folders MUST NOT affect runtime semantics.

Allowed hidden folders:
- `.mystery/`: external descriptor, non-runtime
- `.obsidian/`: viewer configuration, non-runtime
- `.repowise/`: local tooling metadata, non-runtime

---

## 4. Runtime Topology

| Component | Kind | Role |
|---|---|---|
| [[index]] | note | Formation catalog |
| [[log]] | note | Formation timeline |
| `absorb_log.json` | file | Formation audit trail |
| [[schema/RULES]] | note | Genesis contract |
| [[schema/TEMPLATES]] | note | Genesis template catalog |
| [[sources/raw/README]] | note | Matter local inbox descriptor |
| [[sources/remote/README]] | note | Matter remote hint descriptor |
| [[sources/intake/README]] | note | Formation intake descriptor |
| `sources/source-{logical_name}.md` | note family | Formation canonical source registry |

Workflow order is defined in section 10.

---

## 5. Source Area Contract

`sources/` MUST contain only these canonical zones:

| Path | Layer | Rule |
|---|---|---|
| `sources/raw/` | `Matter Layer` | local raw source inbox |
| `sources/remote/` | `Matter Layer` | remote locator hint inbox |
| `sources/intake/` | `Formation Layer` | generated intake artifacts |
| `sources/source-{logical_name}.md` | `Formation Layer` | canonical source manifests |

Source rules:
- Files under `sources/raw/` MUST be treated as raw sources.
- Files under `sources/raw/` MUST NOT be edited by Runtime.
- Each top-level entry in `sources/raw/`, except `README.md`, MUST be treated as one observable local source.
- A top-level file entry in `sources/raw/` MUST be treated as one local source.
- A top-level directory entry in `sources/raw/` MUST be treated as one local source.
- Runtime MUST NOT automatically split a top-level directory entry in `sources/raw/` into multiple canonical sources during bootstrap.
- Files under `sources/remote/` MUST be treated as remote hints, not manifests.
- Files under `sources/intake/` MUST be generated by the LLM and MUST NOT be used as canonical manifests.
- Files matching `sources/source-*.md` MUST be canonical source manifests.

---

## 6. Artifact Contracts

### 6.1 Canonical Source Manifest

Each `sources/source-{logical_name}.md` MUST contain:
- `title`
- `type: source`
- `source_id`
- `logical_name`
- `source_mode`
- `source_locator`
- `raw_path`
- `manifest_path`
- `source_kind`
- `content_format`
- `ingest_template`
- `lifecycle_state`
- `last_ingested`
- `ingested_version`
- `pages_created`
- `pages_updated`
- `forget_policy`
- `semantic_tags`
- `tags`

Canonical source manifest field rules:
- `logical_name` MUST be generated by Runtime as lowercase kebab-case.
- `source_id` MUST be generated by Runtime as `src-{logical_name}` and MUST remain stable across updates.
- `raw_path` MUST be a repository-relative path for `local-raw`, `local-file`, or `local-dir`.
- `raw_path` MUST be `""` for `external-file`, `external-dir`, or `repo-mirror`.
- `source_locator` MUST identify the observable source location for every `source_mode`.
- `source_locator` MUST equal `raw_path` for `local-raw`, `local-file`, or `local-dir`.
- `manifest_path` MUST be the repository-relative path of the canonical manifest.
- `last_ingested` MUST be an ISO 8601 UTC timestamp or `null` before first build.
- `ingested_version` MUST be `sha256:{hex_digest}` computed from the observable source content.
- Directory `ingested_version` MUST be computed from sorted relative paths and file content digests.
- `pages_created` and `pages_updated` MUST contain canonical note paths without `.md`.

Manifest field write-ownership:
- `ingested_version` MUST be written only by build. Bootstrap MUST NOT write `ingested_version`.
- `last_ingested` MUST be written only by build. Bootstrap MUST NOT write `last_ingested`.
- `lifecycle_state` MUST be written by both bootstrap and build, per the rules in §10.
- Bootstrap MUST compute the current source content hash and compare it against the stored `ingested_version` to decide `lifecycle_state`:
  - stored `ingested_version` is `null` or absent → `new`
  - stored `ingested_version` differs from current hash → `changed`
  - stored `ingested_version` equals current hash → unchanged, and bootstrap MUST append a no-op per §10.1
- `pages_created` and `pages_updated` MUST be written only by build.
- `forget_policy` MUST default to `mark-removed-then-reconcile` when no explicit policy exists.
- Runtime MUST NOT create or update a canonical manifest when the source content cannot be observed.

### 6.2 Intake Artifact

Each `sources/intake/intake-{logical_name}.md` MUST contain:
- `title`
- `type: source-intake`
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
- `tags`

Intake artifact lifecycle rules:
- Runtime MUST overwrite `sources/intake/intake-{logical_name}.md` on each bootstrap of the same source.
- Runtime MUST link the intake artifact to the matching canonical manifest when the manifest exists.
- Runtime MAY delete an intake artifact after the matching canonical manifest exists.
- Deleting an intake artifact MUST NOT change canonical source state.

### 6.3 Remote Hint

Each `sources/remote/remote-{logical_name}.md` MUST contain:
- `title`
- `type: source-remote-hint`
- `logical_name`
- `source_mode`
- `source_locator`
- `content_format`
- `ingest_template_hint`
- `semantic_tags`
- `forget_policy`
- `reach_via`
- `credential_ref`
- `hint_status`
- `tags`

Remote hint field rules:
- `source_mode` MUST be `external-file`, `external-dir`, or `repo-mirror`.
- `credential_ref` MUST be `none` when no credential is required.
- `credential_ref` MUST be a symbolic reference when a credential is required.
- `credential_ref` MUST NOT contain credential values.

### 6.4 Generated Knowledge Page

Each generated knowledge page MUST contain:
- `title`
- `type`
- `sources`
- `last_updated`
- `tags`
- `relations`

Shape of `sources`:
- `sources` MUST be a list of objects.
- Each entry MUST contain `source_id`.
- `source_id` MUST match the `source_id` of an existing canonical manifest in `sources/source-{logical_name}.md`.
- Entries MAY contain additional fields (for example `evidence`, `locator`, `notes`) when supported by source content.
- Entries MUST NOT be bare strings.

Each generated knowledge page MUST end with a `## Related` section containing one `[[wikilink]]` per entry in `relations`, in the same order, using the format:
```
- `{relation_type}` [[{target}]]
```
The `## Related` section is the human-readable mirror of the machine-readable `relations` frontmatter. Build MUST keep them in sync: any change to `relations` MUST be reflected in `## Related` before stopping.

Allowed generated page `type` values:
- `entity`
- `concept`
- `playbook`
- `synthesis`

Type-specific required fields:

| Type | Required fields |
|---|---|
| `entity` | `entity_id`, `entity_kind`, `status` |
| `concept` | `domain` |
| `playbook` | `playbook_type`, `status` |
| `synthesis` | `synthesis_kind` |

Entity rules:
- `entity_kind` MUST be derived from source evidence.
- `entity_kind` MUST be lowercase kebab-case.
- If the source does not support a specific kind, `entity_kind` MUST be `custom`.
- Kind-specific fields MAY be added only when supported by source evidence.
- Entity subfolders MAY be created by build using `entities/{entity_kind}/`.
- Entity subfolders MUST NOT be pre-required at `t0`.

---

## 7. Relation Contract

`relations` MUST be the canonical relation model for generated knowledge pages.

Minimal shape:

```yaml
relations:
  - type: uses
    target: concepts/{concept_slug}
```

Relation rules:
- Direction MUST be from the current page to `target`.
- `target` MUST be a canonical note path without `.md`.
- Stable operational relations MUST be encoded in `relations`.
- Prose, tags, and backlinks MUST NOT replace `relations`.

Generated source relation rule:
- Every generated knowledge page MUST declare one `generated_from` relation for each distinct `source_id` present in its `sources` list.
- Each `generated_from` target MUST be the matching canonical manifest path `sources/source-{logical_name}` for the referenced `source_id`.
- `generated_from` relations MUST point to canonical manifests, not intake artifacts, raw sources, or remote hint files.
- Build MUST add any missing `generated_from` relation when a generated knowledge page cites a canonical `source_id` in `sources` but does not yet link to the matching canonical manifest.
- The `## Related` section MUST include the same `generated_from` links in sync with `relations`.

Bidirectionality rule:
- If page A declares `part_of → B`, then B MUST declare `contains → A`.
- Build MUST verify and add the missing half of any `part_of` / `contains` pair when creating or updating either page.

Lateral connection rule:
- Build MUST scan all existing Constellation pages when creating or enriching any page.
- Build MUST add `relations` entries between sibling Constellation pages when declared source evidence supports a direct semantic connection not yet encoded.
- A lateral connection is source-supported when the source explicitly relates two concepts, or when one concept is the cause, prerequisite, solution, instantiation, or interface of another concept described in the same source scope.

Allowed relation types:
- `runs_on`
- `targets`
- `uses`
- `depends_on`
- `generated_from`
- `documents`
- `applies_to`
- `part_of`
- `contains`
- `defines`

---

## 8. Enum Contract

Allowed `source_mode`:
- `local-raw`
- `local-file`
- `local-dir`
- `external-file`
- `external-dir`
- `repo-mirror`

Allowed `source_kind`:
- `config`
- `runtime`
- `workspace`
- `repo`
- `document`
- `dataset`
- `custom`

Allowed `synthesis_kind`:
- overview
- comparison
- bridge

Allowed `content_format`:
- `auto`
- `csv`
- `json`
- `md`
- `html`
- `pdf`
- `docx`
- `txt`
- `repo`

Allowed `lifecycle_state`:
- `new`
- `active`
- `changed`
- `removed`
- `legacy`
- `forget-pending`

Allowed `status`:
- active
- draft
- review-needed
- deprecated
- legacy

Lifecycle rules:
- `new` means the source has a canonical manifest and has not been built yet.
- `active` means the source has been built and remains observable.
- `changed` means the source version differs from the last built version.
- `removed` means Runtime observed that the source is no longer available.
- `forget-pending` means reconcile has been requested for a removed source.
- `legacy` means the source is retained only for historical provenance.
- Build MUST consume only `new` or `changed` manifests.

Status rules:
- `concept` pages MUST NOT use `status` unless explicitly added to the type contract.
- `entity` pages MUST use an allowed `status` value.
- `playbook` pages MUST use an allowed `status` value.
- `synthesis` pages MUST NOT use `status` unless explicitly added to the type contract.

Allowed `forget_policy`:
- `mark-removed-then-reconcile`
- `retain-history`

Allowed `playbook_type`:
- `runbook`
- `decision`
- `howto`
- `troubleshoot`

Allowed `template_confidence`:
- `high`
- `medium`
- `low`

Allowed `builder_request_type`:
- `builder-correction-request`
- `builder-enrichment-request`
- `builder-relation-request`
- `builder-synthesis-request`
- `builder-split-request`
- `builder-tagging-request`
- `builder-merge-request`
- `builder-normalization-request`

Allowed remote hint `reach_via`:
- `auto`
- `mounted-path`
- `unc`
- `http`
- `git`

Allowed remote hint `hint_status`:
- `active`
- `disabled`

Template rule:
- `ingest_template` MUST match [[schema/TEMPLATES]] or be `custom`.

---

## 9. Template Rule

- Templates MUST describe how a source is read.
- Semantic tags MUST describe what a source represents.
- Domain labels such as `architecture`, `network`, `paper`, `policy`, `runbook`, and `inventory` MUST be tags, not templates.

Template selection MUST use this order:
1. existing manifest `ingest_template`
2. explicit hint
3. explicit `content_format`
4. heuristic by extension or structure
5. fallback template
6. if uncertain, set `template_review_needed: true`

---

## 10. Workflows

### 10.1 Bootstrap

Bootstrap registers observable sources. It MUST NOT create Constellation pages.

Allowed triggers:
- manual chat invocation
- scheduled `source-heartbeat`

`source-heartbeat` rules:
- `source-heartbeat` MUST execute the same bootstrap rules as manual bootstrap.
- `source-heartbeat` MUST NOT execute build.
- `source-heartbeat` MUST NOT create Constellation pages.

Local bootstrap MUST:
1. scan `sources/raw/`
2. enumerate top-level entries in `sources/raw/`, excluding `README.md` (identify unregistered or changed items)
3. read source content
4. infer canonical source fields
5. write `sources/intake/intake-{logical_name}.md`
6. write or update `sources/source-{logical_name}.md`
7. set `lifecycle_state` to `new` or `changed`
8. record review scope in Formation and stop

Remote bootstrap MUST:
1. read `sources/remote/remote-{logical_name}.md`
2. verify reachability of `source_locator`
3. if unreachable:
   - append a blocker record to `absorb_log.json`
   - append a human-readable reachability entry to [[log]]
   - MUST NOT create `sources/intake/intake-{logical_name}.md`
   - MUST NOT create `sources/source-{logical_name}.md`
   - MUST NOT update [[index]]
   - stop
4. read source content if reachable
5. infer canonical source fields
6. write `sources/intake/intake-{logical_name}.md`
7. write or update `sources/source-{logical_name}.md`
8. set `lifecycle_state` to `new` or `changed`
9. record review scope in Formation and stop

If bootstrap finds no new source, changed source, or removed source, and no remote blocker, Runtime MUST append a `no-op` entry to `absorb_log.json` and stop without changing [[log]].

### 10.2 Build

Build transforms canonical manifests and Matter into Constellation pages.
Build MUST NOT consume intake artifacts as source registries.

Build MUST consume canonical manifests in `new` or `changed` state.
Build MUST consume `active` manifests when the current Builder invocation resolves Builder requests recorded in Formation.
Builder requests MAY include correction, enrichment, relation, synthesis, split, tagging, merge, or normalization requests.


Build MUST:
1. read [[schema/RULES]]
2. read [[schema/TEMPLATES]]
3. read canonical manifests
4. read latest Formation operation records
5. pick the next manifest using deterministic order: Builder request scope first, then `new`, then `changed`, then `logical_name` ascending
6. read [[index]]
7. read the declared source
8. update pages by topic, not by chronological append
9. create pages only when justified by the concrete noun test or the synthesis rule
10. set touched manifest `lifecycle_state` to `active`
11. set touched manifest `last_ingested` and `ingested_version`
12. run the enrichment pass
13. update `pages_created` and `pages_updated`
14. update [[index]]
15. append to [[log]]
16. append to `absorb_log.json`
17. stop

If no manifest is `new` or `changed` and no unresolved Builder request exists, Build MUST append a `no-op` entry to `absorb_log.json` and stop without changing [[log]].

Absorption rule:
- Build MUST integrate meaning, structure, and relationships.
- Build MUST NOT store facts as loose append-only notes.
- If sources conflict, Build MUST preserve the conflict with source citations and MUST NOT choose one claim without source evidence.

Enrichment rule:
- Build MUST treat page creation as the first pass, not completion.
- Build MUST re-read each touched generated page before stopping.
- Build MUST add source-backed details that improve purpose, mechanism, criteria, tradeoffs, examples, or relations.
- Build MUST prefer enriching an existing page over creating a new page unless the concrete noun test supports a split.
- Build MUST stop enrichment when remaining source material is duplicate, irrelevant, unsupported, or too granular for the wiki.
- A generated page is not build-complete when it only defines a topic and the declared sources support operational detail for that topic.
- After enriching content, Build MUST apply the lateral connection rule and the bidirectionality rule before stopping.

Synthesis rule:
- Build MAY create a `synthesis` page when source-backed integration of at least two distinct Constellation pages or two distinct canonical sources produces a coherent overview, comparison, or bridge that is not adequately represented by a single `entity`, `concept`, or `playbook`.

Concrete noun test:
- Build MUST create a dedicated page when the source clearly describes an `entity`, `concept`, or `playbook`.
- When creating an `entity`, build MUST infer `entity_kind` from the source.
- One source MAY generate multiple Constellation pages when source evidence supports multiple `entity`, `concept`, or `playbook` outputs.



## 11. Update Obligations

Post-bootstrap obligations — on non-no-op bootstrap, Runtime MUST:
- write or update `sources/intake/intake-{logical_name}.md`
- write or update `sources/source-{logical_name}.md`
- set manifest `lifecycle_state` to `new` or `changed`
- update [[index]] to list new or removed canonical manifests
- append to [[log]]
- append to `absorb_log.json`

On unreachable remote bootstrap, Runtime MUST:
- append to [[log]]
- append to `absorb_log.json`
- MUST NOT create intake artifacts
- MUST NOT create canonical manifests
- MUST NOT update [[index]]

Post-build obligations — on non-no-op build, Runtime MUST:
- update touched generated pages
- set touched manifest `lifecycle_state` to `active`
- set touched manifest `last_ingested` and `ingested_version`
- update [[index]] to reflect generated pages created, updated, or removed
- append to [[log]]
- append to `absorb_log.json`

Post-review obligations — on non-no-op review, Reviewer MUST:
- apply mechanical corrections when unambiguous
- append to `absorb_log.json`
- MUST NOT append to [[log]] unless review applied corrections
- MUST NOT modify [[index]] unless aligning an unambiguous desync

Formation operation records MUST let Reviewer derive:
- operation type
- processed sources
- review scope
- pages created
- pages updated
- blockers when present

Bootstrap records MUST contain:
- `operation: bootstrap`
- `job`
- `sources`
- `scope`
- `blockers`
- `operator`

Bootstrap `scope` MUST be an object.
Bootstrap `scope` MAY include:
- `intake_artifacts`
- `canonical_manifests`

Successful bootstrap records MUST list created or updated intake artifacts and canonical manifests in `scope`.
Unreachable remote bootstrap records MUST use an empty `scope`.

No-op records MUST contain:
- `operation: no-op`
- `job`
- `reason`
- empty `sources`, `pages_created`, and `pages_updated`
- `operator`

Evaluation records MAY be written in Formation.

Evaluation records MUST contain:
- `operation: evaluation`
- `job`
- `status`
- `scope`
- `questions_tested`
- `findings`
- `builder_requests`
- `blockers`
- `operator`

Builder requests recorded in Formation MUST contain:
- `request_id`
- `request_type`
- `targets`
- `gap_type`
- `evidence_pointer`
- `recommended_action`
- `requested_by`

`request_id` MUST be stable and unique within the repository.
`request_type` MUST use an allowed `builder_request_type` value.

Build records MAY contain:
- `requests_consumed`
- `requests_resolved`
- `requests_deferred`
- `requests_rejected`

A Builder request MUST be treated as unresolved unless a later Formation record references its `request_id` in `requests_resolved`, `requests_rejected`, or `requests_deferred`.

`builder_requests` recorded in evaluation records MUST be treated as Builder requests recorded in Formation.

Runtime MUST NOT update Matter sources.

---

## 12. Human-Readable Guidance

This section is non-structural.
If this section conflicts with any structured contract above, the structured contract MUST win.

Writing rules:
- Page bodies MAY use the language of the source material.
- Control-plane fields and enums MUST use English.
- Tone MUST be flat, factual, and technical.

Internal links:
- Internal links MUST use double-bracket note paths without `.md`.

Source citation:
- Source citations MUST use `(source: src-{logical_name})`.

Sensitive data:
- Runtime MUST NOT copy secrets or environment-specific sensitive values verbatim.
- Runtime MUST use placeholders such as `[HOSTNAME]`, `[IP-ADDRESS]`, `[FQDN]`, `[TENANT-ID]`, `[ACCOUNT-ID]`, `[API-KEY-REDACTED]`, `[LOCAL-PATH]`, `[REMOTE-LOCATOR]`.

---

## 13. Runtime Invariants

1. Runtime MUST read this file before bootstrap or build.
2. Runtime MUST read [[index]] before build.
3. Runtime MUST re-read a page immediately before editing it.
4. Runtime MUST NOT modify raw sources.
5. Runtime MUST NOT build without a canonical manifest.
6. Runtime MUST NOT use intake artifacts as the canonical registry.
7. Runtime MUST NOT encode stable operational relations only in prose.
8. Remote sources MUST have a locator hint.
9. Runtime MUST NOT invent missing data.
