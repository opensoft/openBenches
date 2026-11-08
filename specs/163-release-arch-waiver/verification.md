# Verification

Local verification on 2026-11-08 in the declared Python bench:

- Release automation: 61 tests passed (53 existing, eight added).
- Release version/source-lock regressions: 14 tests passed.
- Native acceptance prompt contracts: two tests passed.
- Strict OpenSpec validation and git diff whitespace checks passed.
- Exact 1.6.2 selection: 16 required suites; only arch-native waived.
- Neighboring versions and 1.6.2 prereleases retain native Arch requirements.
- Tests reject malformed, duplicate, hosted, unknown or overbroad waiver entries;
  require all other evidence; invalidate old manifest-bound evidence after policy
  changes; and reject missing or altered publisher waiver metadata.
- The publisher integration test uses mocked GitHub calls only. Its printed
  publication message does not mean any real tag or release was created.

This is source/local validation, not live QA acceptance. No readiness variable,
credential, worker, source pin, VERSION or existing tag was changed. The four
remaining external suites still require real protected qualification. CI and
exact-head Codex review are required before the policy lands; PR #246 remains on
its release qualification hold.
