# Plan: Shared helper stack pilot

Implement a separate manual helper queue alongside the docs canary. Mirror
the two literal allowed paths in the Mergify config and CI verifier. Use the
existing Spec Kit Bash feature suite for fast helper checks; preserve the
existing heavy integration suites. Validate the ordered merge parents against
current PR records and exact head/base approval receipts with read-only API
access. Test fail-closed behavior with local Git fixtures.

Open the config as an ordinary PR; the first live helper stack is a separate
acceptance step after review and merge.
