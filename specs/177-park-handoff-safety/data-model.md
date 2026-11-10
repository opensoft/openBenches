# Data model

Public workspace-manifest schema remains version 1. Existing project and leg fields retain meaning. The park record gains internal partial-update scope identifying explicitly selected branch names; it is not rendered as a public manifest field.

A leg identity is its canonical Git common directory plus its exact worktree root and checked-out branch. A partial write replaces selected records while retaining unselected feature blocks from the file at write time. Missing selected replacement on refusal preserves its earlier record. Full reconciliation retains current behavior.
