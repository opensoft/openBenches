# SET-01 evidence

Status: local focused validation passed; full CI/review pending

The wrong-branch and foreign-repository refusal fixtures failed against the
original shared source. After preflight validation was added, all three
focused unittest cases passed, including the successful-push control.
Refusal checks cover both dry-run and actual fixture operation, asserting
unchanged heads, dirty status/content, remote feature refs and prior manifest.

The tests use temporary local Git repositories, bare origins and a disposable
workspace. They do not operate on the operator's handoff repository. The test
command timeout is 90 seconds because the development bench exceeded the first
30-second harness limit; no production timeout or refusal was weakened.

The focused test is wired into the existing shared feature behavior suite.
Full feature/compatibility/bootstrap CI and exact-head Codex results are
separate readback gates. No upstream merge, fleet installation or release is
claimed by this local evidence.
