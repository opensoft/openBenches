# Publication safety and local review

Brett Heap authorized local review of openBenches #315 and openMFA #2,
followed by governed source landing when green. This replaces the unavailable
GitHub bot review for this work; it does not manufacture a bot receipt.

The ten-role local panel reviewed #315 at
1d86af68eb789dd19a643a4b7874c1f41567d790 against
0ac1aa4411669ebf78a62445b953a1d81b8180d4, and openMFA #2 at
12dc8723239f340c7727387b4a4a36c4359aa2cd against its main base.
Architecture, performance, security, QA, static analysis, contracts, integrity,
reliability, simplicity and Bash/Git portability passes were completed.

The consumer review reproduced unrelated-file overwrites through the
manifest's predictable temporary and symlinked manifest directories, plus
direct selector redirection. These are shared writer defects inherited by
the new consumer copy. SET-06 opens directory components without following
symlinks, reads regular destination leaves without following links, creates
temporaries exclusively, publishes descriptor-relatively and only cleans
temporaries whose identity matches the one it created. A canonical workspace
root alias remains supported; symlinks beneath that root are refused.

Both shared and consumer-core selector paths use the same safe publisher
body. The core change remains a declared local upstream deviation.
Resume preflights unsafe selector directories, leaves and occupied temporary
paths before changing either feature leg.

Security re-review independently passed the five original-danger cases:
manifest temporary, both manifest directory levels, selector symlink and
selector hardlink (89.991 seconds). QA reproduced late selector refusal,
then verified the new preflight and preservation assertions. The two focused
pre-reset tests passed in 33.984 seconds.

The corrected consumer suite passed all 37 tests in 63.84 seconds: 27 exact
shared fixture cases and ten consumer-specific cases. The first run caught
two incorrect assertions assuming committed pending files were absent; those
assertions now verify unchanged content/status and the complete rerun passed.
The shape validator passed both unchanged leg pins and all 11 shape digests.
OpenSpec strict and diff whitespace checks passed.

Current-main qualification, exact source/consumer heads, CI runs and landing
readback are recorded separately on the PRs. No queue/ruleset, image activation,
real operator handoff, identity operation, product pin or release is included.
OpenAI feedback remains deferred and neither blocked write was replayed.
