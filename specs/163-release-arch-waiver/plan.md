# Implementation plan

Work in the linked 163-release-arch-waiver feature checkout. Keep VERSION 1.6.1
and all frozen source pins unchanged while landing the policy before the pending
release candidate. Use the existing Python release automation and unittest suite.

1. Add strict optional manifest waiver validation, exact-version suite selection
   and separate waived-not-executed plan/gate metadata.
2. Render exceptions into Actions and publisher notes; verify publisher summary
   metadata against the recomputed gate.
3. Test approval scope, malformed entries, automatic expiry, remaining evidence
   requirements and publisher behavior. Document the exception and restoration.
4. Publish the policy PR with explicit Codex review; retain the release hold.
   Update the existing candidate's qualification notes without tagging it.

## Governed invariants

- `config/release-tests.json` — qualification scope and manifest evidence digest.
- `scripts/release_validation.py` — source-bound selection and fail-closed gate.
- `scripts/publish-validated-release.py` — exact-main publication authority.
- `openspec/` — approved release-policy exception and implementation handoff.

Verification: release automation and release version regression suites, prompt
contracts, diff hygiene, current manifest selection for neighboring versions.
