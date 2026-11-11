# SET-03 evidence

Local validation snapshot, 2026-11-10.

Fresh Codex review of openMFA PR #2 at
fc96c4d3e9778b471a3a04f963f6133f399597b2 found that an already-registered
worktree bypassed origin verification. Disposable fixtures reproduced three
failures: advanced, deleted and unavailable origins all returned success and
uncommitted parked WIP. The unchanged-origin repeat-resume control passed.

The correction verifies each leg's origin and compares its current tip to
the parked commit before the existing-worktree shortcut. Failed fetches
refuse cached tracking refs. All leg checks finish before any reset for the
feature. The dry-run remains a cached, non-writing preview.

After correction, all eleven focused cases passed in 52.305 seconds:
the prior seven park/subset/race cases plus three origin refusal cases and
safe repeated resume. Refusal preserves both local heads, worktree status
and the workspace manifest. Fixtures use local disposable repositories only.
The full local feature suite also passed, ending with all eleven focused
cases green. At 44adc6717af32edae21e85fda7cc849ba1c7592c, PR #312's
published CI passed, including Bash 3.2, Git 2.34.1 and Linux/Windows
PowerShell. Its exact-head Codex review completed without findings.

SET-02 PR #311 at abfd44e8696608ba46e2e180d73b5f97f82526d7 passed
the published Bash, Bash 3.2, Git 2.34.1, PowerShell Linux/Windows, image
regression and fast CI checks. Its exact-head Codex review completed without
findings. Image publishing was skipped, and the neutral queue check did not
admit or merge the PR. SET-03 depends on that source head.

Consumer provenance, hashes and final validation live in openMFA PR #2.
Source PRs remain proposed; no shared-main landing, fleet installation,
operator handoff or release qualification is claimed.
