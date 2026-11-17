# Tasks
- [x] T001 [S] Add guarded execution and offline home resolution. files: base-image/files/codex-profile, base-image/files/codex-exec; verify: python3 -m unittest discover -s devcontainer.test -p test_codex_account_binding.py
- [x] T002 [S] Bind lane child account state and route adapter/installers. files: base-image/files/claude-profile, base-image/Dockerfile, scripts/setup-codex-profiles.sh, scripts/codex-exec, devBenches/scripts/ai-cli-adapter.sh; verify: bash devcontainer.test/test-codex-profile.sh
- [x] T003 [S] Verify account mismatch, missing selection, child inheritance, aliases, API isolation, argument and exit preservation. files: devcontainer.test/test_codex_account_binding.py; verify: python3 -m unittest discover -s devcontainer.test -p test_codex_account_binding.py
- [x] T004 [S] Install guarded launchers and patch generated review scripts reversibly. files: specs/251-codex-lane-account/validation.txt; verify: installation readback and fake-provider smoke tests
