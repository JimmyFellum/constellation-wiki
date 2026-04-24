# Contributing

Keep `main` stable. Use short-lived topic branches for all changes and merge only reviewed, approved work.

## Branches

- Do not commit directly to `main`.
- Create branches with the format `<workspace>/<area>/<topic>`.
- Preferred workspace prefixes:
  - `claude`
  - `codex`
  - `vscode`

Examples:

- `codex/schema/contract-alignment`
- `claude/benchmark/baseline-metrics`
- `vscode/docs/readme-refresh`

## Commits

- Keep commits small and focused.
- Make the first token identify the area touched when possible.
- Good examples:
  - `schema: clarify local raw source unit`
  - `benchmark: align request resolution metrics`
  - `docs: add collaboration workflow`

## Pull Requests

- Open a draft PR early for any non-trivial branch.
- In the PR description, always state:
  - purpose of the branch
  - files or areas touched
  - expected behavioral impact
  - merge criteria

## Contract Changes

- If a change affects `schema/`, say explicitly which agent behavior changes:
  - Source Heartbeat
  - Builder
  - Reviewer
  - Evaluator

- Do not merge contract changes to `main` until the intended behavior is clear and agreed.
