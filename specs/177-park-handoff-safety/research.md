# Research

The current source discovers a paired feature's branch from the spec leg but does not compare the code leg's branch before committing it. A push of the named ref can therefore succeed without carrying the actual code HEAD. Existing preflight covers conflict, rebase and missing remote, not repository/branch agreement.

The workspace writer replaces one complete project block. Filtering the shell discovery list is insufficient for partial updates. Merge unselected blocks at the writer's current-file boundary to protect the push-retry path as well as the initial write.

Use existing Bash/Python-stdlib tooling and disposable Git fixtures. No new runtime package or public schema is needed. The constitution requires one task set per PR; source paths are outside the existing queue pilot allowlists.
