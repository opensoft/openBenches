# Design

## Context

See proposal.md for approval and scope. The trusted automation checkout supplies
the manifest to planning, execution and publication; candidate configuration or a
GitHub readiness variable cannot grant an exception. Its digest already binds
the manifest to source evidence.

## Goals / Non-Goals

Goals: exact stable-version matching, auditable external-suite exceptions, and
automatic expiry outside the approved version. Non-goals: a runtime bypass flag,
waiving hosted checks, skipping other live suites, or changing worker security.

## Decisions

Add optional releaseWaivers metadata to the reviewed manifest. Reject malformed,
duplicate, unknown-suite, hosted-suite, non-stable-version or inapplicable entries.
Match the complete VERSION string, not normalized major/minor or branch names.
Only release mode applies waivers. Preserve the Arch suite at minVersion 1.6.

Use the shared selector for both planning and the final gate. Report applicable
waivers separately from passed evidence as waived-not-executed. Emit the same
metadata in the Actions summary and publisher-generated qualification notes.
Publication recomputes the gate and rejects a mismatching waiver summary.

Alternatives rejected: deleting Arch loses its restoration path; raising its
minimum version waives unrelated 1.6 releases; an environment switch lacks
reviewed version scope and source binding.

## Risks / Trade-offs

- Untested Arch regressions can ship in 1.6.2 -> disclose the accepted limitation.
- Exception leaks into other versions -> exact matching and negative tests.
- A later waiver edit reuses old evidence -> existing manifest digest binding.
- Old main automation still requires Arch -> land the policy change first, then
  refresh the candidate notes and rerun qualification. Do not merge the release
  candidate or tag it while remaining QA prerequisites are absent.

## Migration Plan

Land this policy-only feature without changing VERSION or source pins. Refresh
the existing release candidate with the policy and its explicit notes. Requalify
all remaining suites. Remove the manifest entry once Arch capacity returns;
every other applicable version already requires Arch without waiting for removal.
Reverting the entry restores the Arch requirement for 1.6.2 too.
