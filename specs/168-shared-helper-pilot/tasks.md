# Tasks: Shared helper stack pilot

| Set | Outcome | Task IDs | Parent | Fast verification | Safe intermediate state |
| --- | --- | --- | --- | --- | --- |
| SET-01 | Review-ready narrow helper queue and CI gate | T001–T003 | None | `python3 devcontainer.test/test-stack-ci.py` | Existing docs and release paths remain unchanged |

- [x] T001 [G] Add the opt-in helper queue and exact admission guard. files: `.mergify.yml`, `scripts/stack-ci.py`, `.github/workflows/stack-candidate-heavy.yml`
- [x] T002 Add focused verification and negative Git fixtures. files: `devcontainer.test/test-stack-ci.py`, `scripts/stack-ci.py`
- [x] T003 Document manual admission, evidence and stop criteria. files: `docs/task-set-delivery.md`
- [ ] T004 After the config PR lands, run one approved real code stack and record candidate and landed trees in #250.
