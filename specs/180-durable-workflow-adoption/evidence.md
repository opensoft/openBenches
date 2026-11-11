# Durable adoption source evidence

## Verified locally

- The new complete-source audit failed before adding the repository assets.
- Six adoption tests passed: asset/pointer availability, drift and missing-copy
  negatives, broken-import/pointer negatives, and active-plan/rerun preservation.
- Twelve existing delivery tests and nine five-job coverage-parity tests passed.
- Both copied skills passed skill validation and match the unchanged packaged
  source byte-for-byte: SHA-256
  `0f760d5aaed28c0c9aaa91024834e033e7637a2d82f52ed26f1cca19f5c3b4de`.
- An export built from Git's staged tree, without untracked workstation files,
  passed all six source-adoption tests in an isolated no-network container.
- Actionlint, strict OpenSpec validation, the unchanged image-layer-budget test
  and native Git whitespace checks passed.
- The AGENTS.md active-plan block, its referenced plan and the two existing
  planning templates are unchanged from the PR base.

## Separate gates

Hosted CI and exact-head Codex review are requested on the PR, not inferred from
local tests. The full bootstrap source suite includes the adoption audit and
continues to run normally; its hosted result is a separate gate. No new live
agent session, merge or efficiency canary is claimed by this source audit.

The earlier #250 local-session evidence motivated this change; private raw
transcripts, profile/account details and workstation paths are not committed.
This PR does not alter queue allowlists, release files, app access, rulesets,
credentials, model defaults, submodule pins, original WIP or running benches.
