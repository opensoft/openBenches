# Automated Codex accounts

Run automated work through `codex-exec`. It requires the account selected by CODEX_PROFILE_NAME or the launching lane's CLAUDE_PROFILE_NAME. It never uses the default credential home when selection is missing.

```bash
CODEX_PROFILE_NAME=team-002 codex-exec --json "Review the current diff"
```

Claude profile launches replace stale child Codex selection with their selected profile and resolve the independent Codex registry's credential home. An unavailable cross-provider profile leaves Claude usable, but codex-exec refuses to start a review. Existing sessions can use codex-exec through their existing CLAUDE_PROFILE_NAME; their environment is not rewritten in place.

The guarded launcher verifies that the selected credential email matches profile metadata after credential synchronization, forces ChatGPT/file authentication, clears inherited API-key and access-token overrides, prints the selected account without tokens, and preserves task arguments and exit status. Delegated work inherits the selected credential home. Explicit selection of max-001 is supported; silent fallback to it is refused.

Use `codex-profile home PROFILE` for offline path inspection. Missing or mismatched credentials require reselecting the account or signing in to that profile with `codex-profile login PROFILE`. Do not copy default credentials into another profile to suppress a refusal.

The shared CLI adapter and repaired generated review launchers use the guard. Arbitrary direct vendor-binary calls outside these managed launchers are not intercepted. New Claude launches still export an explicit child credential home for such calls.

Run offline regression tests with:

```bash
python3 -m unittest discover -s devcontainer.test -p test_codex_account_binding.py
bash devcontainer.test/test-codex-profile.sh
```
