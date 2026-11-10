# Plan

One config PR: reproduce stale metadata with an open event snapshot and closed
live readback; add trusted-main preflight using existing scope proof; guard only
event checkout and source validation. Verify all three scopes and negative
open/unmerged/head/file/API cases, existing exact-parent failures, workflow
wiring, and all stack policy suites. Publish without merging or running canaries.
