# Research

- Decision: prefer verified HTTPS on the existing official mirrors after CA bootstrap.
- Evidence: controlled requests to the same Ubuntu metadata URL timed out on HTTP and succeeded on HTTPS; default bridge, MTU-1400 and host-network HTTP comparisons provided no MTU advantage. Host-local receipts retain exact samples.
- Bootstrap: the vanilla Ubuntu image lacks a CA bundle. Do not disable peer verification or introduce an external certificate artifact. Preserve the existing signed-package bootstrap and normalize after it.
- Rejected: larger network/MTU changes, longer timeouts alone, silently accepting missing tools, alternate mirrors and unapproved package/version changes.
- Classification: implementation-only build reliability fix within the existing layered-image contract; no new OpenSpec product or orchestration decision.
