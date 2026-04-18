# Agentic Wiki - Index
> Formation entrypoint.

---

## Wiki Core
- [[schema/RULES]] - builder contract
- [[schema/PROMPT-BUILD]] - builder prompt template
- [[schema/PROMPT-CHECK-SOURCES]] - source heartbeat prompt template
- [[schema/CONTROL]] - reviewer control contract
- [[schema/PROMPT-CONTROL]] - reviewer prompt template
- [[schema/PROMPT-EVAL]] - evaluator prompt template
- [[schema/TEMPLATES]] - ingest template catalog
- [[log]] - human-readable operation timeline
- `absorb_log.json` - structured audit trail
- [[sources/raw/README]] - local raw source inbox
- [[sources/remote/README]] - remote hint inbox
- [[sources/intake/README]] - generated intake artifacts

## Runtime Flow
1. Source heartbeat may be invoked with [[schema/PROMPT-CHECK-SOURCES]]
2. Source heartbeat follows [[schema/RULES]] bootstrap rules
3. Builder is invoked with [[schema/PROMPT-BUILD]]
4. Builder follows [[schema/RULES]]
5. Builder reads [[sources/raw/README]] or [[sources/remote/README]]
6. Builder creates [[sources/intake/README]] artifacts
7. Builder creates `sources/source-{logical_name}.md`
8. Builder creates derived pages in `entities/`, `concepts/`, `playbooks/`, `synthesis/` only after they emerge from sources
9. Builder updates [[index]], [[log]], `absorb_log.json`

## Control Flow
1. Builder follows [[schema/RULES]]
2. Reviewer is invoked with [[schema/PROMPT-CONTROL]]
3. Reviewer follows [[schema/CONTROL]]
4. Reviewer derives scope from Formation records
5. Reviewer applies mechanical fixes or requests Builder correction
6. Reviewer re-runs failed checks until pass or blocker

## Layer State
- `Mystery`: outside runtime
- `Void State`: no generated knowledge has been fixed
- `Genesis Layer`: `schema/`
- `Matter Layer`: `sources/raw/`, `sources/remote/`
- `Formation Layer`: `index.md`, `log.md`, `absorb_log.json`, `sources/intake/`, `sources/source-*.md`
- `Constellation Layer`: not materialized

## Initial Root Contract
- `schema/` - Genesis Layer
- `sources/` - Matter Layer and source-side Formation boundary
- `index.md` - Formation Layer scaffold
- `log.md` - Formation Layer scaffold
- `absorb_log.json` - Formation Layer scaffold

## Formation
No canonical manifest present.

## Constellation
No generated knowledge page present.
