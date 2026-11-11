# Shared Claude/Codex delivery preview (1.7)

This opt-in development preview connects the #250 delivery contract to current
Claude Code and Codex CLI workflows. It is not a product release or a grant of
GitHub App access. No model login, profile token, launcher, hook or permission
bypass is added.

## OpenBenches source adoption

OpenBenches tracks the identical skill under `.agents/skills/task-set-delivery`
for Codex and `.claude/skills/task-set-delivery` for Claude. Its AGENTS.md points
to that skill; a thin CLAUDE.md imports AGENTS.md. Clean checkouts therefore have
the delivery instructions without a workstation-local bootstrap. The existing
active-plan block and planning templates are unchanged.

The packaged skill remains the source of truth. Update both tracked copies
together; `python3 devcontainer.test/test-workflow-adoption.py` rejects drift or
missing pointers and verifies that delivery refresh preserves the active plan.
Other repositories still opt in using the bootstrap below. Source adoption does
not install gh-stack, select a model/account, grant a queue, or qualify a runtime.

## Adopt in a selected project

On a Linux workstation or inside the owning developer bench, use the matching
Tools package:

```bash
setup-openspeckit --repo /absolute/project/path --task-set-delivery
```

For an existing project, a source checkout can stage just the delivery preview
without external initialization, worktree-overlay updates or global agent pointers:

```bash
python3 /absolute/openBenches/devBenches/base-image/files/openspeckit/setup-openspeckit \
  --repo /absolute/project/path --task-set-delivery \
  --skip-init --no-worktrees --no-speckit-registration --preserve-readmes \
  --no-skill-links --no-skill-shape-blocks --no-skill-routing-blocks \
  --no-global-agent-pointers
```

The source command still maintains missing shared protocol files and local Git
excludes as part of the existing bootstrap. Inspect the project's diff before
committing. `--dry-run` previews writes. Existing custom skill directories are
preserved; `--force` uses the bootstrap's broader replacement policy, so do not
use it casually just to refresh one skill.

The installer copies the same portable skill into `.agents/skills`,
`.claude/skills` and legacy `.codex/skills`, adds dedicated managed blocks to
`AGENTS.md`/`CLAUDE.md`, and augments existing plan/tasks templates. It preserves
their handwritten content and first-line repository-shape pointer. Repository
discovery avoids relying on a particular `CLAUDE_CONFIG_DIR` or `CODEX_HOME`.
`--no-repo-agent-pointers` also suppresses the delivery instruction blocks if you
want to stage the skill/templates without changing AGENTS.md or CLAUDE.md.

## Install the pinned authoring tool explicitly

Check `gh stack --version`; the preview expects 0.3.0. If missing, rerun the
bootstrap with `--install-stack-tools`, or explicitly run:

```bash
gh extension install github/gh-stack --pin v0.3.0
```

Normal adoption never installs tools or logs into GitHub. Explicit installation
uses existing `gh` authentication, verifies the result and refuses to replace a
different installed version. It does not configure Mergify or alter rulesets.
The legacy Graphite binary in existing images is neither used nor removed.

## Activate and verify both agents

Start fresh sessions in the adopted repository:

- Claude Code: `/task-set-delivery`
- Codex: `$task-set-delivery`

Ask each agent to identify the loaded skill path and its `1.7-preview.1` metadata,
then plan a current feature with one coherent task set per PR. Verify the set
table, safe intermediate states, focused tests and predecessor relationships.
Instruction/skill installation alone does not prove agent behavior; live
Claude/Codex acceptance is a separate gate before making this the default.

Keep regular Windows Codex Windows-native and WSL/Beta configuration separate.
This PR qualifies the Linux/bench bootstrap, not a native Windows installer or
Windows live activation. A Windows-native checkout can consume the portable
skill through its own `.agents/skills` and repository instructions; do not copy
WSL runtime settings or credentials to activate it.

## CI and merge boundaries

Read [task-set delivery](task-set-delivery.md) and the target repository's current
policy. Use gh-stack for local authoring/push, ordinary dependent PRs and Mergify
for merging. Do not use `gh stack submit`, `link` or `merge` in this rollout.

The workflow does **not** enroll another repository in Mergify or make arbitrary
application code eligible for fast-only CI. Current OpenBenches helper, project
and Wave queues remain narrow allowlists. Mixed, unknown or unqualified scopes
retain full checks. Current-head Codex review remains required where applicable;
past canary waivers are not a standing exemption.

PR #324 addresses stale post-merge Fast CI metadata separately and must be
qualified before another efficiency canary. No canary, merge, bench recreation,
release workflow, version change or tag is part of adopting this source preview.
