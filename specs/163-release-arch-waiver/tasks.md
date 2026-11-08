# Tasks

- [x] T001 [O] Implement exact-version waiver policy and transparent plan/gate metadata — files: `config/release-tests.json`, `scripts/release_validation.py`, `devcontainer.test/test-release-automation.py` — verify: `python3 devcontainer.test/test-release-automation.py`
- [x] T002 [O] Bind publication to waiver metadata and disclose exceptions in notes — files: `scripts/publish-validated-release.py`, `scripts/release_validation.py`, `devcontainer.test/test-release-automation.py` — verify: `python3 devcontainer.test/test-release-automation.py`
- [x] T003 [O] Document scope, restoration and local verification; retain separate policy and release-candidate landing gates — files: `docs/release-automation.md`, `openspec/changes/waive-arch-for-1-6-2/`, `specs/163-release-arch-waiver/` — verify: `git diff --check && openspec validate waive-arch-for-1-6-2 --strict`

Landing: publish this policy separately from PR #246. Refresh that candidate's
qualification notes after the policy lands. Do not merge the candidate or tag a
release until all sixteen remaining suites qualify current main.
