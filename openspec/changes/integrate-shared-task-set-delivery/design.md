# Design

## Context

The bootstrap already owns bounded repository instruction blocks and safe skill
copies. The runtime paths and agent credentials must remain independent.

## Goals / Non-Goals

Ship a preview that both agents can discover in repository-local skill homes,
including when model profiles use custom global configuration directories.
Do not turn every repository into a Mergify/fast-CI participant or run a canary.

## Decisions

- `--task-set-delivery` opts a repository into the shared skill and additive
  instruction/template blocks. Normal bootstrap behavior is unchanged.
- One packaged SKILL.md is copied with the bootstrap's existing safe-copy
  policy into `.agents/skills` and `.claude/skills` (and legacy `.codex/skills`).
  Existing customized skills are preserved unless `--force` is explicit.
- Only dedicated task-set marker blocks are refreshed; handwritten instructions,
  constitution and unrelated template content are preserved.
- `--install-stack-tools` explicitly installs gh-stack v0.3.0 for the invoking
  user if absent. An existing other version causes an actionable stop, not an
  upgrade. Normal bootstrap does not contact GitHub for tools.
- Mergify remains the merger; local authoring uses gh-stack init/add/push and
  ordinary dependent PRs. Source CI and review receipts are not waived.

## Risks / Trade-offs

- Agent instruction discovery is not behavioral acceptance: test fresh Claude
  and Codex sessions separately before making the preview a default.
- Linux bootstrap tests do not prove native Windows installation. Preserve
  Windows-native regular Codex and separate WSL/Beta configuration.
- PR #324 must be qualified before a new efficiency canary; this integration
  does not depend on its code or change queue eligibility.
