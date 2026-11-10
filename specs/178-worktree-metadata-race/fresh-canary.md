# Proposed fresh helper efficiency canary for #250

This is a proposal, not execution or queue admission. Keep #316/#317 dequeued;
retain #318 and its failed first heavy attempt as evidence, not a clean pass.

## Prerequisites

1. Land this ordinary fix PR only after current full CI and applicable exact-head
   review (or a new explicit review waiver). The waivers for #314/#316/#317 do
   not apply to this fix or to new canary PRs.
2. Confirm the deterministic recovery/exclusion fixtures and repeated full Linux
   concurrency suites pass, plus native Windows and both legacy Bash/Git jobs.
   Preserve all five heavy integration jobs and their fail-closed aggregate.
3. Obtain separate approval to run the fresh canary. Verify an empty queue and
   capture current main; do not modify app access, rulesets or release workflows.

## Two task sets on a fresh base

Use gh-stack v0.3.0 for local authoring and push only, with ordinary same-repo PRs.
Do not register a GitHub stack object or rewrite the failed published branches.

- SET-01: replay the test-only option-cardinality assertions from #316 onto
  `ci/stack-helpers/250-retry-option-cardinality`, rooted at the post-fix main.
- SET-02: replay the test-only literal-option assertions from #317 onto
  `ci/stack-helpers/250-retry-literal-option`, based on SET-01's branch.

Only the existing allowlisted helper feature test file changes. Put a standalone
`Stack-CI: helper` in each source commit message before push and in each PR body;
the upper PR also needs `Depends-On: #<lower-number>`. Obtain applicable review
on both exact heads. If Codex quota is unavailable, stop for an explicit waiver.

## Acceptance and stop conditions

Record each exact head/immediate base, test-merge parents and successful fast run
in #250. Verify focused fast CI and policy fixtures run while duplicate ordinary
integration is omitted by positive trusted-main classification. Classifiers and
applicable CodeQL are still expected. Audit source pushes too; distinguish an
untriggered workflow from an observed classifier pass.

After qualification, add the existing manual labels and ordered exact-head
receipts, then enqueue only the top PR through Mergify. Verify the candidate's
two merge parents/heads and allowlisted diff before claiming acceptance.

Require exactly one first-attempt heavy push workflow at that candidate, with
the verifier, full Bash, Git 2.34.1, Bash 3.2, Linux PowerShell, Windows PowerShell
and aggregate all successful. Compare both landed prefix trees and the final
main tree to their tested candidate trees; also check parents and merge timing.
Audit candidate metadata, main pushes and delayed merged metadata for unexpected
duplicate full CI. Missing or uncertain proof must keep full checks, not be
reclassified or bypassed merely to pass the canary.

On failure, stop admission, dequeue the stack, remove its admission labels and
confirm no target movement. Preserve the original failure; do not rerun and call
it a clean one-heavy-run result. No release workflow changes or 1.6.2 tag.
