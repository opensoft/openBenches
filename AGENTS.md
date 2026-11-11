# Repository Agent Instructions

<!-- OPENSPEC-SPECKIT-GLOBAL:START -->
## Shared Agent Protocols

Read `$HOME/.agents/AGENTS.md` for user-global workflow rules, including the
OpenSpec/Speckit protocol and project bootstrap contract.
<!-- OPENSPEC-SPECKIT-GLOBAL:END -->

## Repository Scope

- `workBenches` owns shared launcher and layered-image source files.
- Each bench under `devBenches/` is a separate repository and submodule.
- Run image, container, and Docker validation through the declared bench tooling.
- Preserve unrelated changes in the parent checkout and in bench submodules.

<!-- SPECKIT START -->
Active implementation plan: `specs/181-docker-flight-recorder/plan.md` (bounded, local-only Docker/WSL diagnosis; no automatic recovery).
<!-- SPECKIT END -->

<!-- OPENSPEC-SPECKIT-TASK-SETS:START -->
## Task-set delivery (1.7 preview)

For feature planning, task generation, implementation and PR delivery, use the
shared `task-set-delivery` skill: `.agents/skills/task-set-delivery/SKILL.md`.
Claude can invoke `/task-set-delivery`; Codex can invoke `$task-set-delivery`.
One task set maps to one small PR, with tests and an explicit predecessor.
Keep full CI outside the repository's approved scope. Installing this workflow
does not grant queue access, review waivers, merge authority or release authority.
<!-- OPENSPEC-SPECKIT-TASK-SETS:END -->
