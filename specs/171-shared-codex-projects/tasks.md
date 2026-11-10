# Tasks

## Foundation and US1

- [x] T001 [US1] [O] Implement family catalog projection, identity enrollment, change propagation and isolation fixtures — files: `scripts/codex-project-state.py`, `devcontainer.test/test-codex-project-state.py` — verify: `python3 devcontainer.test/test-codex-project-state.py`

## Desktop integration and US2

- [x] T002 [US2] [O] Add guarded offline synchronization and native desktop launcher — files: `scripts/codex-project-state.py`, `scripts/codex-desktop.ps1`, `devcontainer.test/test-codex-project-state.py`, `devcontainer.test/test-codex-desktop.ps1` — verify: `python3 devcontainer.test/test-codex-project-state.py`
- [x] T003 [US1] [O] Integrate Windows profile setup, cross-platform CI and documentation — files: `scripts/setup-multi-cli-codex-profiles.ps1`, `docs/codex-multi-account-profiles.md`, `.github/workflows/codex-project-sharing.yml` — verify: `python3 devcontainer.test/test-codex-project-state.py`

## US3 and validation

- [ ] T004 [US3] [O] Install tested host-local tooling, restore the Windows account, and record observed verification — files: `specs/171-shared-codex-projects/verification.md`, `specs/171-shared-codex-projects/tasks.md` — verify: `test -s specs/171-shared-codex-projects/verification.md`

## Dependencies

T001 precedes T002; T002 precedes T003 and T004. No agent fan-out is needed. Fixture validation precedes host-local installation and restoration.
