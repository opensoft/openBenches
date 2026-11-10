# Fix qualification and rollout boundary

PR #320, source commit `f2f185cc1e4e4ef3edcb5be9ef68c1d629f7e2a3`.
This is a normal fix PR, not a live helper efficiency canary.

## Reproduction and fix

The fault-injection regression uses the exact exit-128 missing locked-marker
diagnostic from failed #318. Against the unchanged implementation it failed
nine recovery/bound cases plus the child-locale assertion. With the 22-line
production fix, all 14 boundary cases pass: NUL/legacy recovery/exhaustion,
Windows paths, error exclusions, discarded failed stdout, malformed recovery
and candidate-authentication rejection. This is deterministic boundary fault
injection, not a claim of deterministically scheduling the native Git race.

All original parse, ambiguity, scope, live-corroboration and concurrency tests
remain. Recovery is limited to three attempts per format and 100ms backoff;
unrecognized and exhausted failures still throw. No writes are retried.

## Passed hosted source qualification

Three ordinary PowerShell runs passed full Linux (30 scenarios) and native
Windows (7 selected scenarios, including all original 5 state scenarios):

- [Source push](https://github.com/opensoft/openBenches/actions/runs/42899874975)
- [PR opened](https://github.com/opensoft/openBenches/actions/runs/42899888126)
- [PR metadata](https://github.com/opensoft/openBenches/actions/runs/42899917778)

Every Linux run passed the unchanged eight-creator PowerShell/Bash concurrency
scenario on Git 2.56.0 / PowerShell 7.6.9. Windows used Git 2.56.0.windows.4 /
PowerShell 7.6.9 and passed the new recovery cases as well.

Full Bash regression and both legacy jobs also passed:
[ordinary Bash CI](https://github.com/opensoft/openBenches/actions/runs/42899917914).
[Fast CI](https://github.com/opensoft/openBenches/actions/runs/42899918249)
passed all 106 policy/parity fixtures. CodeQL and shared-image regression passed;
publication was correctly not applicable. No CI workflow/action, baseline
command inventory, queue configuration, app access or ruleset was changed.

Local native Windows, policy/parity fixtures, whitespace checks and strict
OpenSpec validation passed. An initial unrestricted local Linux suite hit
Cannot allocate memory in three unrelated cases; its new recovery and real
concurrency scenarios passed, but the full run is not counted as passing.
A disposable rerun limited to 2 CPUs / 2 GiB passed the full 30-scenario suite;
supplementary repetition results are recorded in #250, not substituted for CI.
Running benches were not modified or stopped.

## Remaining gates

Codex review was explicitly requested but returned the account review-usage
limit. That is not review approval; earlier waivers do not carry over to #320.
Require a fresh exact-head review or explicit new waiver before any authorized
merge, and recheck CI/review after each push. This PR is unmerged and unqueued.

The fresh two-PR plan is in [fresh-canary.md](fresh-canary.md). #316/#317 stay
dequeued and #318 remains failed evidence. No new canary was admitted or run.
No release changes or 1.6.2 tag were made.
