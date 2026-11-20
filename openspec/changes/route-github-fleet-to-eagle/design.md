# Design

## Context

The first inventory found 280 active repositories, 238 active workflow definitions and 196 definitions containing Linux hosted selectors. The inventory includes public repositories and OS matrices. Historical workflow records with missing source files are not edited. The current midNet service supports only two pinned workflows and lacks general hosted-image compatibility.

## Decisions

1. Use explicit self-hosted Eagle selectors. Do not rely on collision with GitHub-hosted labels or fallback, which can return jobs to the billing-blocked pool.
2. Keep OS/architecture requirements truthful. Portable Linux jobs migrate first; native Windows/macOS/hardware jobs require compatible execution. The user authorized a disposable Windows VM only without restarting Eagle, Docker or WSL, and confirmed there is no Mac. Native selectors use distinct platform labels; unavailable platforms remain queued.
3. Run general Linux workers inside a fresh rootless Docker backend. Provide only private workspace paths inside that backend for Docker actions/service containers. Sudo and Docker privilege remain within the user namespace, not Eagle's host.
4. Keep host authentication in the Windows controller. No host mounts, shared host Docker socket, bench credentials or private/LAN/metadata access enter general jobs. A separate fleet gateway supports public package endpoints; existing midNet isolation remains intact during migration.
5. Inventory and select repository access explicitly per organization. Preserve public-fork approval controls and deployment environments. Keep existing specialized self-hosted groups intact.
6. Poll repositories with a bounded interval and API budget, then provision only demanded pool/profile capacity. Bound aggregate resources and verify worker/backend/private-volume/registration cleanup before reuse.
7. Prepare narrow workflow PRs, read repository instructions, preserve non-routing content and matrix coverage, request Codex review and merge through repository policy. No protected deployment is approved by the migration.
8. Track the exact detached once-listener exec. Unregister only after its exit; GitHub's forced-delete endpoint is not a busy-job barrier. A root-owned pre-job hook waits for the Windows controller to persist a job deadline before services or action code start. Recovery observes the same exec. STOP stops replenishment and lets an existing listener finish one job; a registered idle listener is not forcibly retired merely because a busy read is false. Recheck the queued candidate before starting a listener so a cancelled demand does not intentionally leave idle capacity.

## Risks and gates

Container jobs differ from hosted VMs: swap, host sysctl, KVM, systemd, native Windows and macOS require explicit compatibility handling. Unsupported jobs stay visibly blocked with exact requirements. Public jobs use fresh user namespaces and retain existing GitHub approval rules. Broadening routing never broadens host credential access.

## Rollback

Retain old selectors and exact blob/head identities in the migration manifest. Revert routing PRs and disable only fleet-owned registrations/groups. Drain active jobs and preserve benches. Never restart shared Docker/WSL to complete migration.


## Ubuntu 24 parallel capacity amendment — 2026-11-20

Brett Heap authorized increasing Eagle Ubuntu 24 capacity, checking available
resources and preserving active jobs, with no application deployment or merge.
Start conservatively with two regular Ubuntu workers in total: the existing
controller and one additional persistent slot. Each retains its qualified
immutable image, private rootless backend, four CPUs and 8 GiB limit. The
specialized .NET worker remains separate and is included in host headroom.

The second slot has its own process lock, state, log and uncertain-create
journal. It reuses the existing executor and exact-listener recovery rules.
It never takes over or rewrites the primary slot's state. Global STOP applies
to both slots; a slot-local STOP drains only the additional slot. Draining
preserves an accepted job and waits for the exact listener to exit before
unregistration and private-resource cleanup.

Before each second-slot worker, reserve both full 8 GiB allocations plus 10 GiB
Linux memory reserve and 4 GiB Windows memory reserve, sufficient host and Docker
backing-store free space, CPU headroom, and fewer than two existing fleet
sandboxes (including guards and uncertain creations). Recheck pressure for
each admission; when headroom is short, pause replenishment without killing
an active worker. Provision only profiles already qualified for Ubuntu 24.
No repository routing, approval, permission, image or test requirement is
broadened by this capacity change.

Acceptance requires actual overlapping GitHub jobs on distinct Ubuntu 24
runner identities, preservation of the previously active job, correct
resource limits and per-job cleanup. Unit tests alone do not establish live
parallel capacity. The additional logon task is additive; no bench, Docker,
WSL or active primary controller restart is required.

### PR review and CI follow-up

PR #336 is stacked on #208. Its fleet paths were absent from existing CI path
filters, so changes need a dedicated pull-request regression workflow. It runs
only tests and watcher syntax validation on the existing Ubuntu 24 route, with
read-only repository permissions and no deployment, publishing or host mutation.
Do not cancel an in-progress validation job when a new head is pushed. Local
Windows runtime tests remain a separate platform check. Review fixes are source
changes only until a subsequent activation is authorized.

The local Codex review identified empty-fleet memory overcommit and duplicate
oldest-job selection. The second slot now reserves both full worker allocations
(26 GiB Linux/20 GiB Windows thresholds), including any outstanding primary budget.
While parallel capacity is enabled, primary Linux admission also reserves its own
full allocation plus the configured reserve. Both controllers exclude active peer
journal job identities; an exclusive shared dispatch lock rechecks and journals the
chosen identity immediately before any guard creation. API validation and job
execution occur outside this short lock. A simultaneous duplicate selection returns
without creating a sandbox. Invalid peer journals fail closed, and only verified
cleanup releases a reservation by changing its journal to ready. These fixes are
source-only and have not been activated on the running host.

### Authorized dedicated fleet-test routing

Brett Heap authorized applying the scoped Eagle route so PR #336 can pass CI,
while preserving active jobs and prohibiting application deployment or merge.
The workflow requests `eagle-linux-ubuntu24-openbenches-fleet-tests`. Host-local
configuration maps that label to the already-qualified Ubuntu 24 image. When a
qualified generic Ubuntu 24 profile already exists, it also offers the dedicated
label so its next disposable worker can accept the test job. Preserve all existing
labels, image pins, pool access, scan entries and resource limits. Add the owning
repository to scanning only if absent; never overwrite concurrent routing edits.
Configuration is reloaded between jobs; this routing change requires no controller
restart or activation of the source-only admission and reservation fixes.

The dedicated route uses a separate stable pull-request concurrency namespace so
an older generic-route run cannot hold its slot. In-progress cancellation remains
disabled; no old run or assigned job is cancelled to perform this migration.
