# CONTROL.md
> QC contract for Builder output.
> Version: 2.6 - 2026-04-12

## 0. Scope

- [[schema/CONTROL]] defines checks, not prompts.
- [[schema/PROMPT-CONTROL]] defines the Reviewer invocation prompt.
- [[schema/RULES]] is the target contract for Builder output.
- Reviewer MUST NOT generate Constellation knowledge from Matter sources.
- Reviewer MUST NOT edit Matter sources.
- Reviewer MUST NOT invent missing data.
- Reviewer MAY read declared Matter sources only to verify evidence and enrichment gaps.
- Reviewer MUST derive review scope from Formation records, not Builder handoff.
- Reviewer MUST ignore `operation: evaluation` records when deriving review scope.
- Evaluation records MAY contain Builder requests, but they are not themselves review scope.
- Reviewer MUST report a Builder traceability finding when scope cannot be derived.
- Reviewer MUST return `pass/no-op` and MUST NOT review older scope when the latest Formation record is `operation: no-op`.
- Reviewer MUST append a Reviewer `no-op` entry to `absorb_log.json` and MUST NOT change [[log]] when reviewing a `no-op` scope.
- If the latest non-evaluation Formation record contains blockers and no reviewable source or page scope, Reviewer MUST append a Reviewer `no-op` entry to `absorb_log.json` and stop.
- Reviewer MUST NOT report a traceability finding for an unreachable remote bootstrap recorded in Formation.

---

## 1. Formation Graph QC

Run after bootstrap.

Check:
- each `sources/intake/intake-{logical_name}.md` links to `sources/source-{logical_name}.md` when the canonical manifest exists
- each canonical manifest is reachable from [[index]]
- generated Markdown Formation artifacts are not graph-isolated unless [[schema/RULES]] explicitly declares them non-linked
- intake artifacts are not treated as canonical manifests

Allowed mechanical fixes:
- add missing intake-to-manifest links
- add missing canonical manifest links to [[index]]
- fix unambiguous broken wikilinks

---

## 2. Build QC

Run after build.

Check:
- each generated knowledge page is reachable from [[index]] or another generated knowledge page
- each generated knowledge page has required fields from [[schema/RULES]]
- stable operational relations are encoded in `relations`
- generated page `sources` cite canonical `source_id` values
- each generated knowledge page has one `generated_from` relation for each canonical source manifest represented in `sources`
- canonical manifests list created and updated generated pages without `.md`
- canonical manifests have correct `lifecycle_state`
- [[index]], [[log]], and `absorb_log.json` reflect the build operation
- Constellation roots do not exist without generated pages

Allowed mechanical fixes:
- add missing links when target identity is unambiguous
- fix `pages_created` or `pages_updated` paths when target identity is unambiguous
- align [[index]], [[log]], or `absorb_log.json` when the intended operation is unambiguous

---

## 3. Content QC

Run after build or scheduled review.

Check:
- contradictions
- orphan pages
- outdated claims
- missing or weak `relations`
- stub pages
- under-enriched pages
- split candidates
- incomplete pages
- forbidden placeholders

Heuristics:
- generated page under 15 lines is a stub candidate
- generated page over 120 lines is a split candidate

Under-enrichment test:
- Reviewer MUST compare each created or updated generated page with its declared source scope when Content QC runs.
- A page is under-enriched when declared sources contain directly relevant operational detail and the page only gives a definition or generic summary.
- Operational detail means purpose, mechanism, criterion, constraint, tradeoff, example, procedure, failure mode, or relation.
- If declared source content cannot be read, Reviewer MUST report a blocker and MUST NOT infer under-enrichment.
- Builder enrichment requests MUST name page path, source_id, missing detail category, and evidence pointer.
- Builder enrichment requests MUST NOT draft replacement Constellation text.

Graph connectivity check:
- Reviewer MUST verify that `part_of` / `contains` pairs are bidirectional across all Constellation pages in scope.
- Reviewer MUST verify that every distinct `source_id` present in the `sources` list of a generated knowledge page is mirrored by a matching `generated_from` relation to the canonical source manifest.
- Reviewer MUST verify that each `sources` entry is an object containing `source_id` and is not a bare string.
- Reviewer MUST identify sibling Constellation pages with no lateral relation when declared source evidence directly connects them.
- A lateral connection is source-supported when the source explicitly relates two concepts, or when one concept is the cause, prerequisite, solution, instantiation, or interface of another concept described in the same source scope.
- Lateral connection gaps MUST be reported as Builder enrichment requests naming both page paths, the missing relation type, and the source evidence pointer.
- A missing `generated_from` relation MUST be treated as a Builder correction request, or as a mechanical fix when the matching canonical manifest is unambiguous from the `sources` field.
- Reviewer MAY apply the missing half of a `part_of` / `contains` pair as a mechanical fix when the inverse relation is unambiguous.

Related section sync check:
- Reviewer MUST verify that every generated knowledge page ends with a `## Related` section.
- Reviewer MUST verify that `## Related` contains exactly one `[[wikilink]]` per entry in `relations`, in the same order.
- A missing or out-of-sync `## Related` section MUST be treated as a mechanical fix when the correct content is unambiguous from `relations`.

Duplicate candidate check:
- Reviewer MUST detect generated pages in scope that appear to represent the same concept, entity, playbook, or synthesis with materially overlapping meaning.
- A duplicate candidate MAY be indicated by near-identical titles, slug variants, highly overlapping sources, highly overlapping relations, or substantially redundant body content.
- Reviewer MUST classify duplicate candidates as one of:
  - `naming-variant`
  - `near-duplicate`
  - `merge-candidate`
- Reviewer MUST NOT merge pages directly when source-derived meaning must be reconciled.
- Reviewer MUST emit a Builder merge or normalization request when a duplicate candidate is confirmed.

Reviewer MUST request Builder correction when source-derived meaning must change.
Reviewer MUST request Builder enrichment when a page is under-enriched or when lateral connections are missing.
Reviewer MAY apply only mechanical non-Matter corrections directly.

---

## 4. Removed Source QC

Run when a canonical manifest is `removed` or `forget-pending`.

Check:
- pages listed in `pages_created` and `pages_updated` still preserve provenance
- pages with at least one active source other than the removed `source_id` are preserved
- pages whose only source is the removed `source_id` are preserved or tagged `review-needed`
- `removed` with `mark-removed-then-reconcile` transitions to `forget-pending`
- `forget-pending` transitions to `legacy`
- `retain-history` transitions to `legacy`

Reviewer MUST NOT delete generated pages automatically.
Reviewer MUST NOT remove facts supported by active sources.
