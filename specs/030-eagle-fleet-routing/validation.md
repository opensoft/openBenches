# Fleet execution evidence

2026-10-21: inventory found 280 active repositories including 12 personal
repositories with no active workflow definitions. 238 checked-in active workflow
workflow records were inventoried, of which 223 source files exist; 15 stale
records whose files no longer exist are recorded separately. The runner-only patch planner produces 201 changed
definitions, 316 selectors and 80 repositories. Those are planned changes, not
completed migrations. Generated default-setup CodeQL jobs need separate treatment.

Selected-repository `Eagle Linux` groups were provisioned in InkRouter (7
repositories), MedxSoft (4), codeXfactory (1), ledgerXfactory (1), and opensoft
(67 initially; 91 after adding 24 repositories with active default-setup CodeQL).
There are now 104 selected repositories across the five groups. Public-repository allowance is enabled only where selected targets include
public repositories. Existing specialist runner groups and midNet groups were
preserved. Host-local group snapshots and configuration retain exact selections.

General-worker image build succeeded with Python 3.12, Node 22, GitHub CLI,
Docker CLI/buildx, sudo, shell tools and Bubblewrap. A disposable rootless engine
proved UID 1001 operation, sudo, the rootless user mapping, a Docker action's
workspace roundtrip, localhost connectivity to a service container, public HTTPS,
private-address denial, Bubblewrap and apt update. Result marker:
`EAGLE_GENERAL_COMPATIBILITY_PASS`. Both probe containers and their anonymous
volumes were removed and absence verified. No bench or host service was restarted.

Twenty focused tests pass for public-only DNS connections, queue selection, busy
registration protection, and byte-preserving direct/matrix/conditional routing.
Actionlint passes for the first changed workflow. Strict OpenSpec validation and
git diff checks pass. The first actual routed GitHub jobs are workBenches
DevBenches Helper Safety push run 39653972082 completed successfully on
`eagle-fleet-ca9d95d84cd5` (job 119409242455, 2026-10-21 18:56:49–18:57:13 UTC).
Cleanup verified its registration, outer containers and private volumes absent
at 18:57:45 UTC. Superseded PR runs 39654023739 and 39655330244 were cancelled;
current-head run 39657321571 remains the landing check.

The next actual job, flutterBench run 39656625395, exposed a missing Docker
Compose plugin in the general image. Its checker was left unchanged. The plugin
was added from the same pinned Docker CLI source, the image rebuilt, and worker
preflight now requires Compose. The failed job was requeued for verification.
A transient zombie error during cleanup of an unassigned subsequent backend
settled to exited; retry verified cleanup at 19:06:18 UTC, without a daemon or
bench restart. Future rootless backends use an outer init and TINI_SUBREAPER.

Routing PRs: workBenches #208, flutterBench #7, goBench #6, phpBench #5,
frappeBench #4. All four bench PRs have clean Codex reviews for their exact
heads; their real CI remains a landing gate. WorkBenches review findings about
predicate preservation, selector scope, complete label matching and pagination
were fixed with regression tests. The subprocess audit finding was addressed by
an explicit executable allowlist, argv-only execution with shell=False, and a
narrow documented audit annotation; unrelated rules remain enabled.

CodeQL inventory: 82 repositories have default setup configured, 29 with supported
languages and 53 currently without a supported language. Routing default setup
requires a separate settings request; group access alone changes no scan route.
The first workBenches request was unsuccessful with settings unchanged; a bounded
reconciled retry is waiting for an eligible online runner. Broad CodeQL migration
is not yet accepted.

Subsequent execution: goBench #6 and phpBench #5 passed their real validation jobs,
received clean Codex reviews for their exact heads, and merged normally as
40cf11cf7eced47aa5e7d2602bb9f19c9a0c7185 and
c5bd941ca198aa8b0694a9b0bd4f6e88cb3220f3. Their default branches now route to Eagle.
WorkBenches current-head run 39657321571 passed on Eagle. Its CodeQL default setup
now reads `runner_type: labeled`, `runner_label: eagle-linux-ubuntu24`, with original
languages, query suite, threat model and schedule preserved. Another repository's
request was rejected while no eligible runner was registered; its settings were
left unchanged. Remaining CodeQL routing needs an eligible-runner window.

A later review correctly identified that forced runner deletion is not a busy-job
barrier. Retirement now observes the exact detached listener exec before
unregistering; STOP does not force removal of an idle registered listener. A
root-owned job-started hook blocks workload code until the Windows controller
has persisted its deadline. An isolated lifecycle probe verified exec creation,
start, running/exited state and cleanup with result `EAGLE_EXEC_LIFECYCLE_PASS`.
The new mode ran phpBench main run 39661180501 successfully; Windows state recorded
`job_assigned: true`, a persisted deadline and `hook_acknowledged: true`. A
supplemental process listing hit a rootless cgroup limitation and was removed in
favor of the authoritative exact exec status. That exec read stopped with exit
code 0; cleanup verified at 19:44:01 UTC. The existing job was preserved during
the observer errors. Gateway provisioning/runtime checks now reject image drift,
and workflow-run discovery paginates all active run pages.

Ubuntu 22 image built successfully against a pinned Ubuntu 22.04 base with the
official runner binaries; its listener version check passed. Nested execution
qualification and workflow activation remain pending for that profile.

Remaining: qualify Ubuntu 22, cloud and other tool profiles; preserve KVM/swap
requirements through qualified execution rather than deleting tests; resolve
native Windows/macOS capacity; land pinned providers before coherent consumer
pin advancement; preserve shape-copy and CI integrity gates; perform and verify
each repository's actual migration. Broad fleet completion is not claimed.

October 22 progress: nine routing PRs have merged after actual CI success:
flutterBench, goBench, phpBench, frappeBench, model-paddle, cloudBench,
gentecBench, simBench and lablinc-zeus-app-spa. The shape provider's full Linux
suite remains running; all thirteen approved consumer updates wait for its
successful merge. Designer has one application assertion failure, admin SPA
fails its production dependency audit, and AdxFactory requires human review.
These gates remain enforced.

The isolated Windows Server 2025 evaluation guest boots with Git 2.56.0,
Python 3.13.17, PowerShell 7.6.7 and Bash 5.3.15 installed. No host restart or
bench restart was required. It is not registered: guest proxy connectivity,
updates, image sealing and disposable-job lifecycle qualification are pending.
The required narrow host firewall rule is prepared but administrator elevation
was rejected by automatic approval policy. Guest public connectivity currently
fails; host-local proxy success is not guest network proof. macOS remains
blocked because no Mac is available. Authorized unused build-cache cleanup
reported 22.04 GB reclaimed without removing running containers or volumes.

Review regression checks now cover arbitrary input/variable runner expressions,
sequence selectors, quoted reusable-workflow pins, versioned Windows audits,
and a gateway validation failure before sandbox creation. Worker PID 1 sleeps
indefinitely until controller cleanup, so the persisted job deadline determines
the maximum runtime. All 31 fleet unit tests pass. Runtime controller refresh
waits for the current job to exit naturally; these source changes do not imply
that the active controller has refreshed.

Follow-up qualification: the Ubuntu 22 image with system PyYAML passed nested
rootless execution, Python 3.10/PyYAML import, Node 22, Compose, bwrap, shared
workspace/container action, public HTTPS, metadata rejection and direct-egress
denial. Its owned engine, guard and anonymous volumes were verified absent
afterward. That immutable image is now enabled as the Ubuntu 22 profile; this
is local qualification, not a completed GitHub job on that profile.

The Windows proxy firewall rule is now present. After assigning a guest-only
static switch address without a default gateway, guest GitHub HTTPS returned
200; LAN CONNECT and metadata HTTP returned 403. Direct TCP to host SMB, LAN
and public internet was denied. Windows Update required explicit machine-level
advanced WinHTTP proxy settings; its scan then succeeded with five security
updates available. Installation and sealed-image/disposable-job checks remain
pending. The native PowerShell suite passed all five Windows state scenarios
inside this guest.

The routing table now includes the current standard hosted labels, keeping
Ubuntu 26, Windows ARM, VS2026 and macOS/Xcode requirements on distinct labels
until those capabilities exist. Quoted scalar expressions retain YAML-sensitive
content, with regressions for hash comments, colon-space text and flow arrays.
All 34 fleet unit tests pass. Label inventory was checked against the
[GitHub standard runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
Guest proxy settings follow the
[Microsoft WinHTTP command reference](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-winhttp).

The extended Ubuntu 22 probe also verified public HTTP and HTTPS from a child
Docker container using the client's generated proxy defaults. Its workspace
round trip, sandboxing, private-destination rejection and cleanup passed again.
The remaining three Speckit Bash selectors now use the matching Eagle Ubuntu
24/22 profiles; the original Git 2.34.1 and Bash 3.2 checks remain intact.

Windows Update download diagnosis found legitimate GET requests carrying
`Content-Length: 0`. The proxy now accepts and strips exactly that empty-body
header; nonzero/ambiguous lengths and all transfer encoding remain denied.
Regression tests cover both allowed GET/HEAD and denied body encodings. All 36
fleet tests and actionlint pass. The Windows-only proxy has this fix and update
downloads are making progress. Linux gateway replacement and the updated
controller/backend wait for natural completion of the active shape test.
Windows evaluation activation succeeded; no Windows runner is registered yet.

The remaining sixteen literal hosted selectors in this repository's cascade,
credential, release and shared-image workflows now route to Eagle. Protected QA
continues to use its existing explicit self-hosted label arrays. Fresh-install
release suites and the shared-image publisher retain their host-swap commands
and select the unavailable `eagle-linux-host-admin` label until an appropriate
isolated host is qualified. Other release suites select Ubuntu 24 normally.
All non-routing workflow values were compared before and after the edits.

All 51 release-automation tests pass. The expanded actionlint check reports the
same five baseline diagnostics, with zero new diagnostics: one existing SC2155
warning and four parser errors for the now-supported GitHub `cache-mode` key.
The cache restrictions and existing scripts were preserved. Current GitHub
workflow syntax documents this key; the local linter's parser predates it.

The inventory contains one raw `fromJSON` runner selector: the protected QA
label array. The transformer now preserves such structured expressions and
the audit flags them for owning-provider review instead of treating arrays as
scalar map keys. Known generated scalar mappings still upgrade idempotently.
All 38 fleet tests pass, including structured-selector preservation/audit cases.


## Second Ubuntu 24 slot — 2026-11-20

User authorization: increase Ubuntu 24 CI capacity, check resources and preserve
active jobs; no application deployment or merge. The canonical controller/backend
matched the installed host source before editing. The existing primary task and
.NET pilot task were preserved. Added `Eagle Ubuntu 24 parallel worker`, a current-user
interactive logon task using native PowerShell 7, a separate mutex, process lock,
state and log, and the existing host-only DPAPI authentication. No bench, WSL,
Docker, image, repository access or workflow restart/change was required.

Activation at 18:46:27 UTC: Windows 32 logical CPUs, available physical memory
16,324,603,904 bytes, CPU 43.55%; Linux MemAvailable 47,084,433,408 bytes;
Docker free 421,542,559,744 bytes; minimum configured Windows disk free
257,447,845,888 bytes. Host total physical memory is 119,880,355,840 bytes.
Admission reserves the full 8 GiB additional backend plus at least 4 GiB Windows
and 10 GiB Linux headroom, four CPU capacity below 80% sampled CPU utilization,
80 GiB disk headroom and no more than two regular fleet sandboxes. Pressure
pauses new admissions and never cancels an assigned job. The primary retains its
existing admission policy; the additional slot only uses existing Ubuntu 24 profiles.

Validation: 50 fleet unit tests passed in py-bench, including 12 added capacity,
resource pressure, profile preservation, drain and primary-journal preservation
tests. All 32 Windows runtime tests (controller, backend, proxy and parallel)
passed. The Windows all-tests command could not load the routing tests because
PyYAML is absent there; those tests passed in the Linux bench. PowerShell watcher
syntax parsed without errors; strict OpenSpec validation and git diff --check passed.
The running primary job was verified before activation and again afterward on
`eagle-fleet-969a4c8f3ed1`: Tenant run 44783182170 / job 136450984527.

Live overlap was verified at approximately 18:54 UTC. GitHub reported both runners
online and busy in group 11 (`Eagle Linux`), with both exact jobs `in_progress`:

- Existing `platform-validate`: [44783182170 / 136450984527](https://github.com/opensoft/Opensoft-Tenant/actions/runs/44783182170/job/136450984527), runner `eagle-fleet-969a4c8f3ed1` (ID 3322), started 18:39:12 UTC.
- Additional `validate`: [44669943383 / 136068233161](https://github.com/opensoft/Opensoft-Tenant/actions/runs/44669943383/job/136068233161), runner `eagle-fleet-fd8427d3ac05` (ID 3325), started 18:53:58 UTC.

The new runner reports Ubuntu 24.04.5 LTS. Both backend resource limits read back
8,589,934,592 bytes and 4,000,000,000 NanoCPUs. The new backend has no host bind
mounts or published ports and `Privileged=false`, `User=rootless`. Both controller
locks were proven exclusive without changing either journal. The installed source
hashes matched the reviewed files, and original configuration objects (profiles,
pools and image pins) were unchanged. Admission with two existing sandboxes
returned `allowed=false`, `reason=worker-limit`. At that sample, Windows available
physical memory was 14,515,978,240 bytes; Linux MemAvailable 44,946,595,840 bytes;
Docker free 414,282,059,776 bytes. The separate .NET pilot remained running.

The additional `validate` job completed successfully at 19:02:06 UTC (8m08s).
The controller observed exact listener exit with code 0 at 19:02:22 and recorded
`cleanup-verified` at 19:02:42. Independent readback at 19:02:57 verified the exact
runner registration, engine, guard and both captured private volumes absent, and
secondary state `ready`. At that same readback the original platform job remained
`in_progress` on its unchanged runner, started at 18:39:12. No assigned job was
cancelled or moved. The second task remains enabled for demand-driven replenishment.

Host-local activation backup, scheduled-task export, installation hashes, overlap
readback and independent cleanup receipt are preserved under
the host-local capacity evidence directory (`$FLEET_CAPACITY_EVIDENCE`). No credentials were copied
into that evidence directory. No application deployment, merge or workflow dispatch
was performed for this capacity acceptance. Source publication is a separate review step; this acceptance did not
merge or deploy application changes.


## PR #336 local review follow-up — 2026-11-20

Local Codex CLI review used the current desktop ChatGPT account, configured model
`gpt-6.1-sol` with high reasoning, against base `265d0bb` and head `be59e9d`.
It reported two P2 findings: empty-fleet admission did not reserve the primary's
outstanding allocation, and independent scans could select the same oldest queued
job. The initial read-only reviewer ran 30 tests but could not run temporary-directory
tests or routing tests because of sandbox restrictions and missing PyYAML.

Fixes reserve both full worker budgets for secondary admission (26 GiB Linux,
20 GiB Windows), add the primary's own budget to its Linux admission when parallel
capacity is enabled, filter jobs reserved by peer journals, and atomically recheck
and reserve a job under a shared dispatch lock before guard creation. Regression
tests cover empty-fleet boundaries, primary memory reserve, peer-journal filtering,
simultaneous preselection of one job and corrupt-journal refusal. The host's running
source and configuration were not changed during this review follow-up.

The original PR had no fleet CI run because existing workflow path filters did not
cover `ops/eagle-fleet/**`. A read-only pull-request workflow now runs the full suite
and parses both PowerShell watchers on the existing Ubuntu 24 route. It does not
cancel in-progress jobs, build or publish images, change host configuration, deploy
or merge. Local tests, final review and exact-head CI results are recorded below.

The review fixes pass 55 fleet tests in py-bench and 37 native Windows runtime
tests. Actionlint, watcher parsing, strict OpenSpec validation and git diff --check
pass. Final local review and the GitHub Actions result are tracked on PR #336 for
the published head; the earlier live acceptance is historical evidence for the
previous installed source, not live acceptance of these unactivated fixes.


## Authorized scoped CI route — 2026-11-20

The user explicitly authorized applying the scoped route and getting PR #336 CI
green, preserving active jobs with no application deployment or merge. On live
readback, generic profiles and the full owning scan list (including openBenches)
had already been restored outside this task. The activation preserved those edits,
all pool/access settings and image pins, and added the dedicated fleet-test profile
plus its label on the already-qualified generic Ubuntu 24 profile. A host-local
backup, before-state snapshots and configuration hashes record the additive change.
No controller restart or activation of source-only scheduler fixes was performed.
The workflow now requests the dedicated label; current-head review and CI results
are tracked on PR #336.
