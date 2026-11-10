# Park handoff integrity: source landing record

Verified 2026-11-10. All six shared implementation PRs merged into
`opensoft/openBenches/main` through ordinary protected merge commits.
The final implementation merge is `23ad5c58963377469fd48bf16f533100fa9040db`,
with tree `0129f3297b33d7a8f20f517695409cbf99349ec8`.

## Authority and review

Brett Heap instructed: "Go ahead and review openBenches #315 and openMFA #2
locally, then land the shared-tooling PRs through the governed process when
green. Keep feedback deferred and don't replay either blocked write."
This authorized local review in place of the unavailable GitHub Codex review.
The earlier quota failures remain historical evidence, not successful bot
receipts. The ten-role panel and focused re-reviews are described in
[evidence-set-06.md](evidence-set-06.md). Commit-bound local reviews and
landing checks were posted on the source PRs and consumer PR.

The local review identified manifest/selector overwrite hazards, unsafe late
selector refusal, and private-file permission widening. SET-06 fixed these
with descriptor-relative atomic publication, no-follow/exclusive temporary
creation, owned-temporary cleanup, early preflight and permission preservation.
Independent security and QA re-reviews passed. No unresolved local finding
remained on the qualified source or consumer heads.

## Immutable landing ledger

Each row records the actual main base, reviewed head, actual merge and tree.
Before merging, checks were green for that head and the synthetic merge's
parents/tree were checked against the current base and intended combined tree.
After merging, the actual merge parents and tree were read back. When main
advanced, the branch was updated and qualification repeated before landing.

| PR | Actual main base | Qualified head | Actual merge | Result tree |
| --- | --- | --- | --- | --- |
| [#310](https://github.com/opensoft/openBenches/pull/310) | `57de8d34ecede2e0474f9899630fe2df609f825b` | `61faee92d4406fc835152fc8e0cfe746fb1ba469` | `ca6534b9b0c8d92fc93dcded54d8234b19837995` | `64d6d5987ff618121418b52bae294e0dd481141d` |
| [#311](https://github.com/opensoft/openBenches/pull/311) | `ca6534b9b0c8d92fc93dcded54d8234b19837995` | `504121c88d2854b68746505c9a63abfb36281c07` | `631d9bf14715902dcaa6bb50db372b1d1beae4a3` | `faf874253c0b05bc9f922790cc82cb3482e96243` |
| [#312](https://github.com/opensoft/openBenches/pull/312) | `631d9bf14715902dcaa6bb50db372b1d1beae4a3` | `aa3b34c77395f666174ab7e52344762589081d24` | `604e6cf998d286481157014955c8945e7461a313` | `e687325d31434e9b48823b762e177b30635403cc` |
| [#313](https://github.com/opensoft/openBenches/pull/313) | `8a1fc47f794b7c195e649dc25427712c8e64b355` | `89b355a46384550fd5f3815827e6bdd229815a8d` | `4ca69752f4badc53e322b2ec26e7cfd6557d8abc` | `3145ef6f4bd0870e73a1c0c8242ddd4bf10be8d5` |
| [#315](https://github.com/opensoft/openBenches/pull/315) | `4ca69752f4badc53e322b2ec26e7cfd6557d8abc` | `c68fda2bbac3de1559dbaf029d19ec87e469980d` | `48df9fb41f49b2fc0580536bf1947eee6ba7706d` | `256169726d592e18533a952291f443676697dc21` |
| [#319](https://github.com/opensoft/openBenches/pull/319) | `48df9fb41f49b2fc0580536bf1947eee6ba7706d` | `8402999509ae44d790c332305c40e7c6d58485fc` | `23ad5c58963377469fd48bf16f533100fa9040db` | `0129f3297b33d7a8f20f517695409cbf99349ec8` |

Unrelated main work, including #320, #321 and #322, was preserved during
qualification. A transient existing worktree-creation fixture failed once
on #310; its exact job rerun passed. A stale synthetic merge ref after
retargeting #311 was correctly refused; updating the branch to actual main
produced a fresh candidate and passing CI. No guard was weakened.

## Final combined-source CI

All runs below belong to qualified SET-06 head
`8402999509ae44d790c332305c40e7c6d58485fc` and completed successfully before
the final source merge:

- [OpenSpeckit Bash regression and compatibility](https://github.com/opensoft/openBenches/actions/runs/42907617886): full regression, Bash 3.2 and Git 2.34.1 passed.
- [Speckit Git PowerShell](https://github.com/opensoft/openBenches/actions/runs/42907618188): Linux and Windows passed.
- [Stack PR fast](https://github.com/opensoft/openBenches/actions/runs/42907617932): candidate/base checks passed.

The final synthetic candidate `f802aea307d14b98dd2b0bc08af4673efeba98ad`
and actual final merge both have parents
`48df9fb41f49b2fc0580536bf1947eee6ba7706d` and
`8402999509ae44d790c332305c40e7c6d58485fc`, and the result tree recorded above.

## Consumer readback and acceptance boundary

[openMFA #2](https://github.com/opensoft/openMFA/pull/2) remains draft/open at
`502b1d74266f19f34b497414ec88a525c42cfe7c`. It passed all 38 tests locally
(78.02 seconds) and in [runtime-tooling CI](https://github.com/opensoft/openMFA/actions/runs/42907202214)
(25.19 seconds), plus [validation](https://github.com/opensoft/openMFA/actions/runs/42907202254)
and SonarCloud. Its final [local review](https://github.com/opensoft/openMFA/pull/2#pullrequestreview-5849918165)
is attached to that head.

Readback against the landed source confirmed four helper files and the
canonical 28-case fixture are byte-for-byte copies of immutable producer
`46a867b62322939beae62eb1f21d27fcf6ce1720`, now an ancestor of main. The
consumer core selector publisher body matches the shared publisher; its
deviation remains declared. All consumer Bash syntax checks passed. The
original two leg pins and all 11 shape-copy digests remain unchanged.

This closes T015–T017 for source implementation, reviewed consumer preparation
and source landing evidence. It does not merge the consumer, install tooling
into active benches, advance product pins, qualify live MFA, deploy runtime
code, publish a release, ratify frozen origin metadata or archive the change.
No administrator override, direct default-branch push, queue/ruleset change or
operator park/resume occurred. OpenAI feedback remains deferred and neither
previously blocked write was replayed.
