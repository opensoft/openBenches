# Plan

Reproduce the recorded diagnostic with deterministic fault injection and prove
red. Add a bounded fresh-read recovery solely for the missing locked marker,
then verify success, exhausted retries, unrelated errors, partial records and
candidate corroboration. Keep legacy fallback and the real eight-creator test.
Run full PowerShell Linux/native Windows, Bash/legacy integration, existing policy
regressions and strict OpenSpec checks. Open an unqueued normal PR and request
Codex review. Record a proposed fresh canary in #250 without running it.
