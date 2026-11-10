# Fast merged metadata evidence

## Reproduction

PR #322 event retained an old test merge after retargeting to main. Live GitHub
readback confirms the same head `3cf30a49804e55d715cf0bf072634e20b9594c12`
merged as `8a1fc47f794b7c195e649dc25427712c8e64b355` with one scoped modified file.
Four new regression tests failed before implementation and pass afterwards.

## Local qualification

Disposable py-bench container, no network; no running bench modified:

- Stack policy: 36 passed, including all three metadata scopes and negative cases.
- Project policy: 31 passed.
- Helper policy: 34 passed.
- Helper integration parity: 9 passed; all five integration jobs unchanged.
- OpenSpec strict validation passed. Initial OpenSpec validation hit a local
  Node ENOMEM; retry with bounded Node worker/heap settings passed.
- Actionlint and native Git whitespace checks passed.

This is a config PR, not a live canary. Hosted checks and exact-head Codex review
are separate gates. No merge, release, app-access or ruleset changes authorized.
