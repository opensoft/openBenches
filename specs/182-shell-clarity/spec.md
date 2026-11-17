# Shared Speckit shell clarity
Parent maintenance task: opensoft/openXwallet#82, separately from completed wallet#73.

Clarify conditional tests in the canonical shared Bash overlay. Preserve the existing branch numbering, discovery, ownership, park/resume refusals, project-emitted output, state and cleanup behavior. Do not install the candidate globally, rebuild a bench, operate on active sessions, or change runtime limits, CI checks or billing.

This is implementation maintenance of the existing shared workspace contract. No new workflow, capability, grant, configuration or product requirement is introduced.

For malformed or overflowing numeric input, the same builtin comparison can identify itself as test instead of [ in the shell-generated stderr prefix. Preserve numeric parsing, refusal status and project-authored messages; record and review that diagnostic command-name difference explicitly.
