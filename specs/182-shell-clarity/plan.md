# Implementation plan
Use Bash double-bracket conditionals for unary string and file predicates. Retain the explicit test builtin for exact string equality/inequality, because inherited nocasematch must not relax branch, path or project identity checks. Use the explicit decimal test builtin for numeric comparisons: unlike double-bracket arithmetic, it does not reinterpret leading-zero numbers, empty or untrusted strings as arithmetic expressions. Retain the same operands, operators, order, short circuiting and command boundaries.

Qualify canonical source before publishing and port the bounded predicate repairs into installed consumer variants without upgrading unrelated bootstrap behavior. Preserve source provenance and every existing assertion. Run shell syntax, compare static diagnostics, differential predicate probes and the existing shared-overlay fixture suites. Publish and verify provider main before updating consumers.

Qualification includes arbitrarily long numeric selections, leading zeroes, signed values, empty values and arithmetic-shaped strings. The builtin command name in invalid-integer diagnostics changes from [ to test; no project-authored diagnostic, parsing decision, refusal or exit status is changed by that spelling difference.

Candidate qualification: all nine scripts pass bash syntax; 728 optional ShellCheck bracket diagnostics are removed with every other diagnostic code/count unchanged. Differential probes agree on 2,400 numeric comparison results, 560 string results and 63 file-attribute results. Of the numeric probes, 1,536 malformed or overflowing pairs exercised the recorded builtin-name diagnostic difference. Existing overlay suites, independent review, hosted CI and actual-main acceptance remain pending.

Independent review found that the first candidate relaxed equality under inherited nocasematch. That candidate is retained in history and is not accepted. The corrected recipe uses 292 unary double-bracket predicates, 179 strict-decimal test predicates and 257 case-sensitive string test predicates. Existing fixture results on the first candidate do not qualify this correction; rebind review and rerun affected fixtures.

The new exact-branch regression fails on the first candidate and passes on the correction, using real bare/local fixture worktrees. It also verifies the sourced helper leaves nocasematch enabled for its caller. The source directive in that regression names the actual canonical dependency for static analysis; no rule is disabled.

## Follow-up for the Sonar shell predicate rule

The complete wallet analysis reports the explicit test command introduced by
the first predicate pass. Use double brackets for shell counters, lengths,
statuses and values already normalized to signed decimal. Use double brackets
for closed flags and punctuation markers. For raw names and configuration
values, combine the quoted comparison with quoted literal prefix removal.
This preserves exact case and metacharacters under inherited nocasematch and
leaves the caller's shell options intact.

Retain the strict integer builtin at input boundaries that accept decimal
strings, including interactive selections and stored WIP depths. These values
can contain leading zeroes or lie outside the supported signed range. The
mtime comparisons retain the strict builtin at their external-output boundary.
This preserves their return statuses and diagnostics.

Qualify canonical source first with the existing fixture suites and compare
the installed versions without upgrading the hooks. Main analysis supplies
the actual finding dispositions.
