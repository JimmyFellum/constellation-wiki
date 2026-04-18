# constellation-wiki

> From void to knowledge universe — domain-agnostic agentic wiki built, reviewed, and evaluated by LLM agents.

This repo is the **void scaffold** of the Constellation Wiki system: a schema, a set of prompt contracts, and a cosmological architecture that lets LLM agents build a structured knowledge universe from any set of raw sources.

You bring the documents. The agents build the universe.

---

## How it works

The system is organized in layers, from the outside in:

| Layer | What it is |
|---|---|
| `Mystery` | External governance — the meta-principle, outside runtime |
| `Void State` | This repo at rest — no knowledge generated yet |
| `Genesis` | `schema/` — the immutable contracts and prompt templates |
| `Matter` | `sources/raw/`, `sources/remote/` — your raw input documents |
| `Formation` | `index.md`, `log.md`, `absorb_log.json`, manifests — the control plane |
| `Constellation` | `entities/`, `concepts/`, `playbooks/`, `synthesis/` — generated knowledge |

Four agentic roles drive the lifecycle:

- **Source Heartbeat** — discovers and registers sources, creates canonical manifests
- **Builder** — reads manifests and raw sources, generates and enriches knowledge pages
- **Reviewer** — QC on Builder output, applies mechanical fixes, emits correction requests
- **Evaluator** — tests answerability of the wiki, emits semantic improvement requests

Each role is invoked by loading its prompt from `schema/`. Agents communicate only through the filesystem — no shared context between roles.

---

## How to use

1. Clone this repo
2. Drop your raw documents into `sources/raw/`
3. Invoke **Source Heartbeat** using `schema/PROMPT-CHECK-SOURCES.md` with `ROOT_PATH` set to your repo root
4. Invoke **Builder** using `schema/PROMPT-BUILD.md`
5. Invoke **Reviewer** using `schema/PROMPT-CONTROL.md`
6. Invoke **Evaluator** using `schema/PROMPT-EVAL.md`
7. Repeat from step 4 until the system converges

The wiki inflates from void. Each cycle enriches it further.

---

## Key files

| File | Purpose |
|---|---|
| `schema/RULES.md` | Master build contract — all normative rules |
| `schema/TEMPLATES.md` | Ingest template catalog by source format |
| `schema/CONTROL.md` | Reviewer QC contract |
| `schema/PROMPT-BUILD.md` | Builder prompt template |
| `schema/PROMPT-CHECK-SOURCES.md` | Source Heartbeat prompt template |
| `schema/PROMPT-CONTROL.md` | Reviewer prompt template |
| `schema/PROMPT-EVAL.md` | Evaluator prompt template |
| `index.md` | Formation entrypoint — live index of all wiki contents |
| `log.md` | Human-readable operation timeline |
| `absorb_log.json` | Structured audit trail of all agent operations |

---

## What this repo is not

- Not a wiki with content — it is the schema to build one
- Not tied to any domain — works with technical docs, research papers, runbooks, codebases, or any structured source material
- Not a finished product — it is a void scaffold, ready to inflate
