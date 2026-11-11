# Design

## Context

PR 326 delivered the opt-in installer. Local activation is not durable source
adoption: pointers and their target assets must land together.

## Goals / Non-Goals

Make this repository self-contained for delivery-skill discovery. Do not change
other repositories, the active feature plan, runtime defaults or merge authority.

## Decisions

Use regular tracked SKILL.md files under `.agents/skills/task-set-delivery` and
`.claude/skills/task-set-delivery`, matching the packaged skill byte-for-byte.
Copies work in Windows checkouts without requiring symlink support. Keep legacy
`.codex` copies generated/ignored. A thin CLAUDE.md imports AGENTS.md; add only the
existing managed task-set block to AGENTS.md, leaving its active-plan block intact.

Existing tracked planning templates already carry the one-task-set-per-PR rule;
do not duplicate or rewrite them. The packaged skill remains the source of truth.
Source-adoption tests reject missing/divergent assets and broken pointers, and
exercise the existing delivery updater against a temporary repository copy to
verify active-plan preservation and rerun stability.

## Risks / Trade-offs

- Tracked copies can drift: parity checks run through the ordinary source Bash
  suite, with triggers covering both copies and instruction files.
- A partial bench test mount is not a source checkout: the additional source
  audit runs only when the complete repository audit script is present. Existing
  runtime bootstrap tests and all five integration jobs remain unchanged.
- Clean-source tests are not new live model or merge-canary acceptance.
