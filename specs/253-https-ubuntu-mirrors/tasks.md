# Tasks: HTTPS Ubuntu Mirrors

Task set: `https-ubuntu-mirror-transport`. Parent: the preserved operational source snapshot. No PR or integration landing is authorized by these local tasks.

## Phase 1 - Transport fixtures

- [X] T001 [US1] [S] Add fixture tests for the exact normalization block, covering legacy/deb822, official ports, comments, unrelated hosts, missing files and idempotence — files: `scripts/tests/test_ubuntu_mirror_transport.py` — verify: `python3 scripts/tests/test_ubuntu_mirror_transport.py`

## Phase 2 - Shared-base correction

- [X] T002 [US1] [O] Add verified HTTPS normalization after the existing CA bootstrap and before later package operations — files: `base-image/Dockerfile` — verify: `python3 scripts/tests/test_ubuntu_mirror_transport.py`

## Phase 3 - Operational rebuild and runtime acceptance

- [X] T003 [US2] [O] Rebuild required shared layers and three benches using declared wrappers; inspect actual utilities/browser and encrypted sources — files: `specs/253-https-ubuntu-mirrors/tasks.md` — verify: `test -n "$MIGRATION_EVIDENCE_ROOT" && test -f "$MIGRATION_EVIDENCE_ROOT/https-rebuild-verified.json"`
- [X] T004 [US2] [O] Run Wave checks, repeat-start identity, UID, bind, CLI and reaping checks; confirm hold and rollback invariants — files: `specs/253-https-ubuntu-mirrors/tasks.md` — verify: `test -n "$MIGRATION_EVIDENCE_ROOT" && test -f "$MIGRATION_EVIDENCE_ROOT/native-cutover-verified.json"`

## Dependencies and Strategy

T001 precedes T002; T003 follows passing transport tests; T004 follows the corrected image rebuild. Independent family builds may run in parallel under the existing storage and memory guards. No subagents are needed for this bounded correction.

## Acceptance Readback

All required shared layers and the three Brett-personalized images were rebuilt and verified on the native engine. The six mirror fixtures pass; every personalized image has the official Ubuntu sources on HTTPS with CA trust present. The Python testing utilities and an offline Chromium launch pass. The declared AI CLI image checker passes without writing the version manifest.

All three Wave launcher checks and repeat-start checks pass with the same container identities, Brett UID 1000, init enabled, writable host-project access and zero zombies after the reaping test. Python and cloud use the explicit `/workspace/projects` host bind; Microsoft 365 uses its declared parent home bind and accesses projects at `/home/brett/projects`. No project data was copied into Docker.

The existing host Dev Containers CLI 0.80.1 could not recognize Docker 29 start events. The installed host launcher was upgraded to the official 0.91.0 package while retaining the old installation. This was an operational compatibility correction, not a daemon or WSL restart. Native startup's scheduled task is ready and its manual test returned zero; a full Windows reboot and a human Wave GUI click remain unperformed.

Final private receipts are `https-rebuild-verified.json`, `native-ai-cli-contract-check.json`, `native-runtime-status.json`, `native-cutover-verified.json` and `windows-final-readback.json` under the operator-owned evidence root. All five CI/diagnostic-watchdog tasks remain disabled, both CI STOP markers remain present, Docker Desktop remains stopped/manual and its original data disk remains retained. The Windows readback had 180.81 GiB free on C:, above the 100 GiB reserve. No PR, source integration landing or CI release was performed.
