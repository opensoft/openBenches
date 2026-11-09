# Plan: replace Graphite authoring

Document local `gh-stack` authoring, atomic branch push, and ordinary PR
publication with explicit predecessor bases and `Depends-On` markers. Verify
the branch order and fresh-branch fallback against a disposable Git remote.
Record the new workflow in #250; live Mergify activation and canary evidence
remain separate from this documentation change.
