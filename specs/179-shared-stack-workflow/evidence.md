# Source qualification

Change: integrate-shared-task-set-delivery; milestone 1.7, #250.

## Local checks

Disposable py-bench containers with networking disabled; active benches and
workstation profile directories were not changed.

- Nine real-fixture delivery tests passed: both agents receive the same skill;
  handwritten instructions/shape pointer/templates survive; reruns are
  idempotent; custom skills require explicit force; non-adoption and dry-run
  preserve delivery state; symlink targets and incomplete marker content are
  protected; pointer opt-out is respected; tool installation is explicit,
  pinned and verified; another installed version is not replaced.
- A disposable packaged-path smoke test used the installed command and asset
  locations from the Dockerfile and produced matching Claude/Codex skill copies.
- Skill-creator validator passed in the container. Native Python lacked PyYAML;
  validation was completed with the container dependency, not skipped.
- Nine helper coverage-parity tests passed; all five integration jobs remain.
- Base-image Dockerfile wiring, actionlint, Bash syntax, Python compilation,
  strict OpenSpec validation and native Git whitespace checks passed.
- Full existing bootstrap regression passed, including the nine new delivery
  tests (`GREEN: OpenSpec bootstrap regression test passed`).

## Boundaries and remaining acceptance

No image was rebuilt or bench recreated. No native Windows installer or live
Claude/Codex behavior was qualified. The regular Windows runtime and WSL/Beta
configuration remain separate. No new model credentials, hooks, queue rules,
CI eligibility, app grants, ruleset changes or release workflow changes.

Hosted checks and exact-head Codex review are separate PR gates. No merge or
canary is authorized by this source PR. After review/merge approval, adopt in
one selected current development project, start fresh agent sessions, verify
skill provenance and small task-set output, and only then propose live stacks.
PR #324's metadata fix must qualify before another efficiency canary.
