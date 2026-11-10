# Verification

Run from the feature worktree in the declared development bench:

```sh
openspec validate fix-park-handoff-integrity --strict
bash devBenches/devcontainer.test/test-speckit-git-feature.sh
bash devBenches/devcontainer.test/test-speckit-git-compat.sh
bash devBenches/devcontainer.test/test-openspeckit-bootstrap.sh
```

These fixtures use temporary local repositories and manifests. Do not test park against the real operator workspace. Publish SET-01 through SET-05 as ordinary dependent PRs, with exact heads/bases and review receipts. Do not widen Mergify pilot scope or infer release qualification.
