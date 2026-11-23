# Tasks: HTTPS Ubuntu Mirrors

Task set: `https-ubuntu-mirror-transport`. Parent: the preserved operational source snapshot. No PR or integration landing is authorized by these local tasks.

## Phase 1 - Transport fixtures

- [X] T001 [US1] [S] Add fixture tests for the exact normalization block, covering legacy/deb822, official ports, comments, unrelated hosts, missing files and idempotence — files: `scripts/tests/test_ubuntu_mirror_transport.py` — verify: `python3 scripts/tests/test_ubuntu_mirror_transport.py`

## Phase 2 - Shared-base correction

- [X] T002 [US1] [O] Add verified HTTPS normalization after the existing CA bootstrap and before later package operations — files: `base-image/Dockerfile` — verify: `python3 scripts/tests/test_ubuntu_mirror_transport.py`

## Phase 3 - Operational rebuild and runtime acceptance

- [ ] T003 [US2] [O] Rebuild required shared layers and three benches using declared wrappers; inspect actual utilities/browser and encrypted sources — files: `specs/253-https-ubuntu-mirrors/tasks.md` — verify: `test -n "$MIGRATION_EVIDENCE_ROOT" && test -f "$MIGRATION_EVIDENCE_ROOT/https-rebuild-verified.json"`
- [ ] T004 [US2] [O] Run Wave checks, repeat-start identity, UID, bind, CLI and reaping checks; confirm hold and rollback invariants — files: `specs/253-https-ubuntu-mirrors/tasks.md` — verify: `test -n "$MIGRATION_EVIDENCE_ROOT" && test -f "$MIGRATION_EVIDENCE_ROOT/native-cutover-verified.json"`

## Dependencies and Strategy

T001 precedes T002; T003 follows passing transport tests; T004 follows the corrected image rebuild. Independent family builds may run in parallel under the existing storage and memory guards. No subagents are needed for this bounded correction.
